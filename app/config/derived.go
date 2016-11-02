// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package config

import (
	"crypto/sha512"
	"fmt"
	"time"

	"github.com/bradfitz/gomemcache/memcache"

	"google.golang.org/cloud/datastore"
	"google.golang.org/cloud/logging"
	"google.golang.org/cloud/pubsub"
	"google.golang.org/cloud/storage"
)

const (
	CookieSeconds = int(CookieDuration / time.Second)
	EnsureHost    = CanonicalHost != ""
)

var (
	TokenSpec = TokenKeys[DefaultTokenKeyID]
)

var (
	BlobClient   *storage.Client
	CacheClient  *memcache.Client
	DataClient   *datastore.Client
	LogClient    *logging.Client
	PubsubClient *pubsub.Client
)

type Queue struct {
	Name    string
	Timeout time.Duration
	Key     []byte
}

func init() {
	for keyID, spec := range TokenKeys {
		if spec.Hash == nil {
			spec.Hash = sha512.New384
		}
		if spec.ID == 0 {
			spec.ID = keyID
		} else if spec.ID != keyID {
			panic(fmt.Errorf("config: mismatching token key ID %d provided for map entry %d", spec.ID, keyID))
		}
	}
}
