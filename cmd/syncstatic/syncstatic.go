// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"context"
	"crypto/sha256"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"google.golang.org/cloud/storage"
)

const (
	archivePeriod = 14 * 24 * time.Hour // 14 days
)

var files = map[string]*File{}

type File struct {
	data   []byte
	digest string
	exists bool
}

func exit(format string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, "ERROR: "+format+"\n", args...)
	os.Exit(1)
}

func walkDirectory(path string, prefix string) {
	l, err := ioutil.ReadDir(path)
	if err != nil {
		exit("couldn't read path %s: %s", path, err)
	}
	for _, info := range l {
		if info.IsDir() {
			walkDirectory(filepath.Join(path, info.Name()), prefix)
			continue
		}
		fpath := filepath.Join(path, info.Name())
		rpath := fpath[len(prefix):]
		data, err := ioutil.ReadFile(fpath)
		if err != nil {
			exit("couldn't read path %s: %s", fpath, err)
		}
		files[rpath] = &File{
			data:   data,
			digest: fmt.Sprintf("%x", sha256.Sum256(data)),
		}
	}
}

func main() {

	if len(os.Args) != 4 {
		fmt.Println("Usage: syncstatic LOCAL_PATH BUCKET_NAME STORAGE_PREFIX")
		os.Exit(1)
	}

	localPath, err := filepath.Abs(os.Args[1])
	if err != nil {
		exit("couldn't resolve the LOCAL_PATH parameter: %s", err)
	}

	walkDirectory(localPath, localPath+"/")

	bucketName := os.Args[2]
	storagePrefix := os.Args[3]
	if !strings.HasSuffix(storagePrefix, "/") {
		storagePrefix += "/"
	}

	ctx := context.Background()
	client, err := storage.NewClient(ctx)
	if err != nil {
		exit("couldn't initialise cloud storage client: %s", err)
	}

	bucket := client.Bucket(bucketName)
	q := bucket.Objects(ctx, &storage.Query{Prefix: storagePrefix})

	now := time.Now()
	for {
		attrs, err := q.Next()
		if err != nil {
			if err == storage.Done {
				break
			}
			exit("unexpected error whilst retrieving synced files from the bucket %s: %s", bucketName, err)
		}
		if attrs.Metadata != nil {
			digest := attrs.Metadata["sha256"]
			file, exists := files[attrs.Name[len(storagePrefix):]]
			if exists {
				if file.digest == digest {
					file.exists = true
				}
			} else if now.Sub(attrs.Updated) > archivePeriod {
				fmt.Printf(">> Removing: %s/%s\n", bucketName, attrs.Name)
				err = bucket.Object(attrs.Name).Delete(ctx)
				if err != nil {
					exit("couldn't remove file from bucket: %s", err)
				}
			}
		}
	}

	paths := []string{}
	for path, _ := range files {
		paths = append(paths, path)
	}

	sort.Strings(paths)

	for _, path := range paths {
		file := files[path]
		if file.exists {
			continue
		}
		fmt.Printf(">> Updating: %s/%s%s\n", bucketName, storagePrefix, path)
		w := bucket.Object(storagePrefix + path).NewWriter(ctx)
		w.ObjectAttrs.ACL = []storage.ACLRule{{storage.AllAuthenticatedUsers, storage.RoleOwner}}
		w.ObjectAttrs.Metadata = map[string]string{"sha256": file.digest}
		_, err := w.Write(file.data)
		if err != nil {
			exit("couldn't write to %s: %s", path, err)
		}
		err = w.Close()
		if err != nil {
			exit("couldn't close the write to %s: %s", path, err)
		}
	}

}
