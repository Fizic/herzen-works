package main

import (
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

type Task struct {
	ID          int64     `json:"id"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	Status      string    `json:"status"`
	CreatedAt   time.Time `json:"createdAt"`
}

type storage struct {
	mu    sync.RWMutex
	tasks map[int64]Task
	seq   int64
	file  string
}

func newStorage(file string) (*storage, error) {
	s := &storage{tasks: make(map[int64]Task), file: file}
	if err := s.load(); err != nil {
		if !errors.Is(err, os.ErrNotExist) {
			return nil, err
		}
	}
	return s, nil
}

func (s *storage) load() error {
	f, err := os.Open(s.file)
	if err != nil {
		return err
	}
	defer f.Close()
	var list []Task
	if err := json.NewDecoder(f).Decode(&list); err != nil {
		return err
	}
	var maxID int64
	for _, t := range list {
		s.tasks[t.ID] = t
		if t.ID > maxID {
			maxID = t.ID
		}
	}
	s.seq = maxID
	return nil
}

func (s *storage) persist() error {
	tmp := s.file + ".tmp"
	if err := os.MkdirAll(filepath.Dir(s.file), 0o755); err != nil {
		return err
	}
	f, err := os.Create(tmp)
	if err != nil {
		return err
	}
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	var list []Task
	for _, t := range s.tasks {
		list = append(list, t)
	}
	if err := enc.Encode(list); err != nil {
		f.Close()
		return err
	}
	f.Close()
	return os.Rename(tmp, s.file)
}

func (s *storage) nextID() int64 {
	s.seq++
	return s.seq
}

func basicAuth(next http.Handler, user, pass string) http.Handler {
	realm := "Restricted"
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		u, p, ok := r.BasicAuth()
		if !ok || !secureCompare(u, user) || !secureCompare(p, pass) {
			w.Header().Set("WWW-Authenticate", "Basic realm=\""+realm+"\"")
			http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func secureCompare(a, b string) bool {
	ha := sha256.Sum256([]byte(a))
	hb := sha256.Sum256([]byte(b))
	return ha == hb
}

func writeJSON(w http.ResponseWriter, code int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	if v != nil {
		_ = json.NewEncoder(w).Encode(v)
	}
}

func readJSON(r *http.Request, v interface{}) error {
	if ct := r.Header.Get("Content-Type"); ct != "application/json" && !strings.HasPrefix(ct, "application/json;") {
		return fmt.Errorf("unsupported content type: %s", ct)
	}
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	return dec.Decode(v)
}

func listTasks(s *storage) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		s.mu.RLock()
		defer s.mu.RUnlock()
		var list []Task
		for _, t := range s.tasks {
			list = append(list, t)
		}
		writeJSON(w, http.StatusOK, list)
	}
}

func createTask(s *storage) http.HandlerFunc {
	type req struct {
		Title       string `json:"title"`
		Description string `json:"description"`
		Status      string `json:"status"`
	}
	return func(w http.ResponseWriter, r *http.Request) {
		var in req
		if err := readJSON(r, &in); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		if strings.TrimSpace(in.Title) == "" {
			http.Error(w, "title is required", http.StatusBadRequest)
			return
		}
		if in.Status == "" {
			in.Status = "Pending"
		}
		s.mu.Lock()
		id := s.nextID()
		t := Task{ID: id, Title: in.Title, Description: in.Description, Status: in.Status, CreatedAt: time.Now().UTC()}
		s.tasks[id] = t
		if err := s.persist(); err != nil {
			s.mu.Unlock()
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		s.mu.Unlock()
		writeJSON(w, http.StatusCreated, t)
	}
}

func updateTask(s *storage) http.HandlerFunc {
	type req struct {
		Title       *string `json:"title"`
		Description *string `json:"description"`
		Status      *string `json:"status"`
	}
	return func(w http.ResponseWriter, r *http.Request) {
		idStr := strings.TrimPrefix(r.URL.Path, "/api/tasks/")
		id, err := strconv.ParseInt(idStr, 10, 64)
		if err != nil {
			http.Error(w, "invalid id", http.StatusBadRequest)
			return
		}
		var in req
		if err := readJSON(r, &in); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		s.mu.Lock()
		defer s.mu.Unlock()
		t, ok := s.tasks[id]
		if !ok {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		if in.Title != nil {
			t.Title = *in.Title
		}
		if in.Description != nil {
			t.Description = *in.Description
		}
		if in.Status != nil {
			t.Status = *in.Status
		}
		s.tasks[id] = t
		if err := s.persist(); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		writeJSON(w, http.StatusOK, t)
	}
}

func deleteTask(s *storage) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		idStr := strings.TrimPrefix(r.URL.Path, "/api/tasks/")
		id, err := strconv.ParseInt(idStr, 10, 64)
		if err != nil {
			http.Error(w, "invalid id", http.StatusBadRequest)
			return
		}
		s.mu.Lock()
		defer s.mu.Unlock()
		if _, ok := s.tasks[id]; !ok {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		delete(s.tasks, id)
		if err := s.persist(); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	}
}

func getTask(s *storage) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		idStr := strings.TrimPrefix(r.URL.Path, "/api/tasks/")
		id, err := strconv.ParseInt(idStr, 10, 64)
		if err != nil {
			http.Error(w, "invalid id", http.StatusBadRequest)
			return
		}
		s.mu.RLock()
		defer s.mu.RUnlock()
		t, ok := s.tasks[id]
		if !ok {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		writeJSON(w, http.StatusOK, t)
	}
}

func routes(s *storage, user, pass string) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		fmt.Fprintln(w, "Task Management System (Go stdlib)")
	})
	mux.Handle("/api/tasks", basicAuth(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			listTasks(s).ServeHTTP(w, r)
		case http.MethodPost:
			createTask(s).ServeHTTP(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	}), user, pass))

	mux.Handle("/api/tasks/", basicAuth(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			getTask(s).ServeHTTP(w, r)
		case http.MethodPut:
			updateTask(s).ServeHTTP(w, r)
		case http.MethodDelete:
			deleteTask(s).ServeHTTP(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	}), user, pass))

	return logging(mux)
}

func logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s", r.Method, r.URL.Path, time.Since(start))
	})
}

func main() {
	addr := getenv("TASK_ADDR", ":8080")
	user := getenv("TASK_USER", "admin")
	pass := getenv("TASK_PASS", "admin123")
	dataFile := getenv("TASK_DATA", filepath.Join(os.TempDir(), "tasks.json"))

	rand.Seed(time.Now().UnixNano())

	s, err := newStorage(dataFile)
	if err != nil {
		log.Fatalf("storage init: %v", err)
	}

	srv := &http.Server{
		Addr:         addr,
		Handler:      routes(s, user, pass),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	log.Printf("listening on %s (basic auth user=%s)", addr, user)
	go func() {
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("server: %v", err)
		}
	}()

	// Graceful shutdown on SIGINT/SIGTERM could be added if needed.
	// Block forever.
	select {}
}

func getenv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
