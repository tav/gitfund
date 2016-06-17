// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"crypto/sha512"
	"hash"
	"net/http"
	"runtime/debug"
	"strconv"
	"strings"
	"time"

	"google.golang.org/appengine"
)

var DevServer = false

var (
	canonicalHost  string
	cookieDuration time.Duration
	cookieSeconds  int
	ensureHost     bool
	pageRenderers  []Renderer
	router         func(*Context)
	routes         RouteMap
	tokenKey       []byte
	tokenKeyID     int
	tokenHash      func() hash.Hash
	tokenKeys      TokenKeys
)

type Config struct {
	CanonicalHost  string
	CookieDuration time.Duration
	PageRenderers  []Renderer
	Router         func(*Context)
	Routes         RouteMap
	TokenKeys      TokenKeys
}

// raise301 can be used as a value to panic in order to interrupt the control
// flow and raise a 301 Permanent Redirect.
type raise301 struct {
	url string
}

// raise404 can be used as a value to panic in order to interrupt the control
// flow and raise a 404 Not Found.
type raise404 struct{}

type Route struct {
	Admin     bool
	Anon      bool
	Cron      bool
	Handler   func(*Context)
	Renderers []Renderer
	Task      bool
	XSRF      bool
}

type Renderer func(c *Context, content []byte)

type RouteMap map[string]*Route

func Dispatch(w http.ResponseWriter, r *http.Request) {
	c := NewContext(w, r)
	defer func() {
		if err := recover(); err != nil {
			c.buffer.Reset()
			if redir, ok := err.(raise301); ok {
				c.headers = map[string]string{
					"Location": redir.url,
				}
				c.status = 301
			} else if _, ok := err.(raise404); ok {
				c.serve404()
			} else {
				c.Errorf("%v\n%s", err, string(debug.Stack()))
				c.serve500()
			}
		}
		cl := false
		ct := false
		hdrs := w.Header()
		for k, v := range c.headers {
			switch strings.ToLower(k) {
			case "content-length":
				cl = true
			case "content-type":
				ct = true
			}
			hdrs.Set(k, v)
		}
		var out []byte
		if c.written {
			out = c.output
		} else {
			out = c.buffer.Bytes()
		}
		clen := len(out)
		if !cl {
			hdrs.Set("Content-Length", strconv.FormatInt(int64(clen), 10))
		}
		if !ct {
			hdrs.Set("Content-Type", "text/html; charset=utf-8")
		}
		for _, v := range c.cookies {
			hdrs.Set("Set-Cookie", v)
		}
		w.WriteHeader(c.status)
		if clen != 0 {
			w.Write(out)
		}
	}()
	if !DevServer {
		badURL := false
		if r.TLS == nil {
			badURL = true
		} else if ensureHost && r.Host != canonicalHost && !(c.IsCronRequest() || c.IsTaskRequest()) {
			badURL = true
		}
		if badURL {
			host := canonicalHost
			if host == "" {
				host = r.Host
			}
			if r.Method == "GET" || r.Method == "HEAD" {
				url := r.URL
				url.Scheme = "https"
				url.Host = host
				c.RaiseRedirect(url.String())
			} else {
				c.RaiseRedirect("https://" + host + "/")
			}
		}
	}
	path := r.URL.Path
	if !strings.HasPrefix(path, "/") {
		c.serve404()
		return
	}
	path = path[1:]
	elems := strings.Split(path, "/")
	if path == "" {
		elems[0] = "/"
	}
	if route, ok := routes[elems[0]]; ok {
		for _, elem := range elems[1:] {
			if elem != "" {
				c.Args = append(c.Args, elem)
			}
		}
		route.Handler(c)
		return
	}
	c.serve404()
}

func Init(c *Config) {
	DevServer = appengine.IsDevAppServer()
	canonicalHost = c.CanonicalHost
	if canonicalHost != "" {
		ensureHost = true
	}
	cookieDuration = c.CookieDuration
	if cookieDuration == 0 {
		cookieDuration = 14 * (24 * time.Hour)
	}
	cookieSeconds = int(cookieDuration / time.Second)
	pageRenderers = c.PageRenderers
	router = c.Router
	routes = c.Routes
	tokenKeyID = 0
	tokenKeys = c.TokenKeys
	for keyID, spec := range tokenKeys {
		if keyID > tokenKeyID {
			tokenKeyID = keyID
		}
		if spec.Hash == nil {
			spec.Hash = sha512.New384
		}
	}
	tokenKey = tokenKeys[tokenKeyID].Key
	tokenHash = tokenKeys[tokenKeyID].Hash
	http.HandleFunc("/", Dispatch)

}
