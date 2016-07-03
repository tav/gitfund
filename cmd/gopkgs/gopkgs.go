// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"bytes"
	"encoding/json"
	"go/build"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"

	"github.com/tav/golly/fsutil"
	"github.com/tav/golly/log"
	"github.com/tav/golly/optparse"
	"github.com/tav/golly/process"
	"golang.org/x/tools/go/vcs"
)

var (
	svcDir   = ""
	vcsTypes = []string{"git", "hg"}
)

var vcsArgs = map[string][]string{
	"git": []string{"rev-parse", "HEAD"},
	"hg":  []string{"identify", "--id", "--debug"},
}

type Diff struct {
	local  string
	stored string
}

type Entry struct {
	Src string `json:"src"`
	Rev string `json:"rev"`
	VCS string `json:"vcs"`
}

type Manifest struct {
	Packages map[string]*Entry `json:"packages"`
	Toplevel []string          `json:"toplevel"`
}

func checkDeps(ignore string) {
	expected := genDeps(ignore, false)
	out, err := ioutil.ReadFile(getManifestPath())
	if err != nil {
		log.Fatal(err)
	}
	if bytes.Equal(out, expected) {
		return
	}
	local := &Manifest{map[string]*Entry{}, []string{}}
	err = json.Unmarshal(expected, &local)
	if err != nil {
		log.Fatal(err)
	}
	stored := &Manifest{map[string]*Entry{}, []string{}}
	err = json.Unmarshal(out, &stored)
	if err != nil {
		log.Fatal(err)
	}
	diffs := map[string]Diff{}
	for k, l := range local.Packages {
		s := stored.Packages[k]
		if s == nil {
			diffs[k] = Diff{l.Rev, "-"}
		} else if l.Rev != s.Rev {
			diffs[k] = Diff{l.Rev, s.Rev}
		}
	}
	for k, s := range stored.Packages {
		l := local.Packages[k]
		if l == nil {
			diffs[k] = Diff{"-", s.Rev}
		} else if l.Rev != s.Rev {
			diffs[k] = Diff{l.Rev, s.Rev}
		}
	}
	for pkg, diff := range diffs {
		log.Errorf("Revision mismatch for package %s\n\n\tExpected: %s\n\t   Found: %s\n", pkg, diff.stored, diff.local)
	}
	process.Exit(1)
}

func contains(xs []string, s string) bool {
	for _, elem := range xs {
		if elem == s {
			return true
		}
	}
	return false
}

func genDeps(ignore string, writeFile bool) []byte {

	ctx := &build.Context{
		BuildTags: []string{"appenginevm"},
		Compiler:  build.Default.Compiler,
		GOARCH:    "amd64",
		GOOS:      "linux",
		GOPATH:    build.Default.GOPATH,
		GOROOT:    build.Default.GOROOT,
	}

	buf := &bytes.Buffer{}
	gopath := filepath.SplitList(ctx.GOPATH)
	pkgs := map[string]*Entry{}
	repos := map[string]bool{}
	seen := map[string]bool{}
	skip := strings.Split(ignore, ",")
	toplevels := []string{}
	workspaces := []string{}

	var findPackages func(string, bool)

	findPackages = func(path string, toplevel bool) {
		pkg, err := ctx.ImportDir(path, 0)
		if err != nil {
			log.Fatal(err)
		}
		for _, imp := range pkg.Imports {
			if !strings.Contains(imp, ".") {
				continue
			}
			if seen[imp] {
				continue
			}
			exists := false
			wspace := ""
			for _, wspace = range workspaces {
				path := filepath.Join(wspace, imp)
				exists, _ = fsutil.Exists(path)
				if exists {
					break
				}
			}
			if !exists {
				log.Fatalf("unable to find import %s on the GOPATH: %v", imp, gopath)
			}
			exists = false
			root := imp
			vcs := ""
			for root != "." {
				path := filepath.Join(wspace, root)
				for _, vcs = range vcsTypes {
					if exists, _ = fsutil.Exists(filepath.Join(path, "."+vcs)); !exists {
						continue
					}
					break
				}
				if exists {
					break
				}
				root = filepath.Dir(root)
			}
			if !exists {
				log.Fatalf("unable to find git/hg directory for %s", filepath.Join(wspace, imp))
			}
			if !repos[root] {
				if err = os.Chdir(filepath.Join(wspace, root)); err != nil {
					log.Fatal(err)
				}
				buf.Reset()
				cmd := exec.Command(vcs, vcsArgs[vcs]...)
				cmd.Stdout = buf
				cmd.Stderr = os.Stderr
				if err = cmd.Run(); err != nil {
					log.Fatal(err)
				}
				rev := strings.TrimSpace(buf.String())
				pkgs[root] = &Entry{
					Rev: rev,
					VCS: vcs,
				}
				repos[root] = true
			}
			seen[imp] = true
			setToplevel := toplevel
			if toplevel && !contains(skip, root) {
				toplevels = append(toplevels, imp)
				setToplevel = false
			}
			findPackages(filepath.Join(wspace, imp), setToplevel)
		}
	}

	for _, workspace := range gopath {
		workspaces = append(workspaces, filepath.Join(workspace, "src"))
	}

	findPackages(svcDir, true)

	sort.Strings(toplevels)
	for _, pkg := range skip {
		delete(pkgs, pkg)
	}

	for pkg, entry := range pkgs {
		root, err := vcs.RepoRootForImportPath(pkg, false)
		if err != nil {
			log.Fatal(err)
		}
		entry.Src = root.Repo
	}

	out, err := json.MarshalIndent(&Manifest{pkgs, toplevels}, "", "  ")
	if err != nil {
		log.Fatal(err)
	}

	out = append(out, '\n')
	if writeFile {
		if err = ioutil.WriteFile(getManifestPath(), out, 0644); err != nil {
			log.Fatal(err)
		}
	}

	return out

}

func getManifestPath() string {
	return filepath.Join(svcDir, ".gopkgs.json")
}

func main() {

	opts := optparse.New("Usage: gopkgs [OPTIONS] SERVICE_DIR\n")
	opts.SetVersion("0.1")

	check := opts.Flags("-c", "--check").Bool(
		"Verify that the packages on GOPATH match the .gopkgs manifest")

	ignore := opts.Flags("-i", "--ignore").Label("REPOS").String(
		"Comma-delimited package repos to ignore")

	os.Args[0] = "gopkgs"
	args := opts.Parse(os.Args)
	if len(args) != 1 {
		opts.PrintUsage()
		process.Exit(1)
	}

	cwd, err := os.Getwd()
	if err != nil {
		log.Fatalf("couldn't get working directory path: %s", err)
	}
	svcDir = filepath.Join(cwd, args[0])

	if *check {
		checkDeps(*ignore)
	} else {
		genDeps(*ignore, true)
	}

}
