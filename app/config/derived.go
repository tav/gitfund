// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package config

import (
	"crypto/sha512"
	"fmt"
	"time"

	"golang.org/x/oauth2/jwt"
	"google.golang.org/cloud/storage"
)

const (
	CookieSeconds = int(CookieDuration / time.Second)
	EnsureHost    = CanonicalHost != ""
)

var (
	GCS = &jwt.Config{
		Email:      GCloudEmail,
		PrivateKey: GCloudPrivateKey,
		Scopes:     []string{storage.ScopeReadWrite},
		TokenURL:   "https://accounts.google.com/o/oauth2/token",
	}
	TokenSpec = TokenKeys[DefaultTokenKey]
)

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
