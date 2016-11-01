// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"crypto/sha256"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"google.golang.org/cloud/storage"
)

const staticCacheDuration = 2 * time.Hour

var (
	staticCache = map[string]*staticEntry{}
	staticMutex = sync.RWMutex{}
)

type staticEntry struct {
	data       []byte
	etag       string
	mimetype   string
	modified   time.Time
	validUntil time.Time
}

func getMimetype(path string) string {
	idx := strings.LastIndex(path, ".")
	if idx == -1 {
		return "application/octet-stream"
	}
	switch path[idx+1:] {
	case "css":
		return "text/css; charset=utf-8"
	case "js":
		return "text/javascript"
	case "txt":
		return "text/plain; charset=utf-8"
	case "png":
		return "image/png"
	case "jpg", "jpeg":
		return "image/jpeg"
	case "gif":
		return "image/gif"
	case "svg":
		return "image/svg+xml"
	case "pdf":
		return "application/pdf"
	case "zip":
		return "application/zip"
	default:
		return "application/octet-stream"
	}
}

func serveStatic(c *Context, spec *Static) {
	path := spec.File
	if path == "" {
		if len(c.pathArgs) == 0 {
			c.serve404()
			return
		}
		path = filepath.Join(append([]string{spec.Directory}, c.pathArgs...)...)
	}
	if DevServer {
		info, err := os.Stat(filepath.Join("static", path))
		if err != nil {
			c.serve404()
			return
		}
		staticMutex.RLock()
		entry, exists := staticCache[path]
		staticMutex.RUnlock()
		if !exists || !entry.modified.Equal(info.ModTime()) {
			data, err := ioutil.ReadFile(path)
			if err != nil {
				c.serve404()
				return
			}
			entry = &staticEntry{
				data:     data,
				mimetype: getMimetype(path),
				modified: info.ModTime(),
			}
			staticMutex.Lock()
			staticCache[path] = entry
			staticMutex.Unlock()
		}
		c.SetResponseHeader("Content-Type", entry.mimetype)
		c.DirectOutput(entry.data)
		return
	}
	staticMutex.RLock()
	entry, exists := staticCache[path]
	staticMutex.RUnlock()
	if !exists || time.Now().After(entry.validUntil) {
		data, err := c.BlobRead(filepath.Join("static", path))
		if err != nil {
			if err != storage.ErrObjectNotExist {
				c.Errorf("web: unexpected error trying to serve static file %s: %s", path, err)
			}
			c.serve404()
			return
		}
		entry = &staticEntry{
			data:       data,
			etag:       fmt.Sprintf("%x", sha256.Sum256(data)),
			mimetype:   getMimetype(path),
			validUntil: time.Now().Add(staticCacheDuration),
		}
		staticMutex.Lock()
		staticCache[path] = entry
		staticMutex.Unlock()
	}
	expiration := spec.Expiration
	if expiration == 0 {
		expiration = staticCacheDuration
	}
	c.SetResponseHeader("Content-Type", entry.mimetype)
	if c.ResponseCachePublic(entry.etag, expiration) {
		c.SetResponseStatus(304)
		return
	}
	c.DirectOutput(entry.data)
}
