// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"fmt"
	"os"

	"github.com/bradfitz/gomemcache/memcache"
	"github.com/tav/gitfund/app/config"
	"google.golang.org/cloud/datastore"
	"google.golang.org/cloud/logging"
	"google.golang.org/cloud/pubsub"
	"google.golang.org/cloud/storage"
)

// We save references to the various clients as globals in the config package so
// that they can be accessed by the packages that this web package depends on —
// so as to not cause circular dependencies.
func initCloud(c *Context) {
	blobClient, err := storage.NewClient(c)
	if err != nil {
		panic(fmt.Errorf("web: failed to initiate blobstore client: %s", err))
	}
	dataClient, err := datastore.NewClient(c, config.AppID)
	if err != nil {
		panic(fmt.Errorf("web: failed to initiate datastore client: %s", err))
	}
	logClient, err := logging.NewClient(c, config.AppID, "app")
	if err != nil {
		panic(fmt.Errorf("web: failed to initiate logging client: %s", err))
	}
	pubsubClient, err := pubsub.NewClient(c, config.AppID)
	if err != nil {
		panic(fmt.Errorf("web: failed to initiate pubsub client: %s", err))
	}
	host := os.Getenv("MEMCACHE_PORT_11211_TCP_ADDR")
	if host == "" {
		host = "localhost"
	}
	port := os.Getenv("MEMCACHE_PORT_11211_TCP_PORT")
	if port == "" {
		port = "11211"
	}
	cacheClient := memcache.New(fmt.Sprintf("%s:%s", host, port))
	config.BlobClient = blobClient
	config.CacheClient = cacheClient
	config.DataClient = dataClient
	config.LogClient = logClient
	config.PubsubClient = pubsubClient
}
