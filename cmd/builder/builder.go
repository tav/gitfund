// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"archive/tar"
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"

	"github.com/tav/golly/fsutil"
	"github.com/tav/golly/log"
	"gopkg.in/yaml.v2"
)

var vcsCheckout = map[string]string{
	"git": "git checkout -q",
	"hg":  "hg update -r",
}

type GoManifest struct {
	Packages map[string]GoPackage `json:"packages"`
	Toplevel []string             `json:"toplevel"`
}

type GoPackage struct {
	Src string `json:"src"`
	Rev string `json:"rev"`
	VCS string `json:"vcs"`
}

type FileSpec struct {
	Src    string
	Dst    string
	Ignore []string
}

type Spec struct {
	Commands []string
	Files    []*FileSpec
	Include  []string
	Type     string
}

func build(appID string, path string) {

	moduleDir, err := filepath.Abs(path)
	if err != nil {
		log.Fatal(err)
	}

	moduleID := filepath.Base(moduleDir)
	moduleImage := appID + "/" + moduleID + ".generator"
	rootDir := filepath.Dir(moduleDir)
	envDir := filepath.Join(rootDir, "environ")
	buildRoot := filepath.Join(envDir, "build")
	buildDir := filepath.Join(buildRoot, moduleID)
	imgDir := filepath.Join(buildDir, "image")

	// Ensure docker is running.
	status := getOutput("docker-machine", "status")
	if status != "Running" {
		log.Fatalf("docker is not running and is returning a status of %q", status)
	}

	// Ensure docker environment variables are available.
	if os.Getenv("DOCKER_HOST") == "" {
		log.Fatal("could not find DOCKER_HOST: please run `eval $(docker-machine env)`")
	}

	// Create the environ/build directory if necessary.
	if exists, _ := fsutil.Exists(buildRoot); !exists {
		err = os.Mkdir(buildRoot, 0777)
		if err != nil {
			log.Fatal(err)
		}
	}

	// Remove the module build directory if it exists already.
	if exists, _ := fsutil.Exists(buildDir); exists {
		err = os.RemoveAll(buildDir)
		if err != nil {
			log.Fatal(err)
		}
	}

	// Create a pristine module build directory.
	err = os.Mkdir(buildDir, 0777)
	if err != nil {
		log.Fatal(err)
	}

	// Set the header for the new Dockerfile.
	buf := &bytes.Buffer{}
	fmt.Fprintf(buf, "FROM  %s/buildbase\n\n", appID)

	// Include the base Dockerfile for the module if it exists.
	baseDocker := filepath.Join(envDir, moduleID+".Dockerfile")
	if exists, _ := fsutil.FileExists(baseDocker); exists {
		content := read(baseDocker)
		buf.Write(content)
		buf.Write([]byte{'\n'})
	}

	// Read the build spec for the module.
	file := read(filepath.Join(envDir, moduleID+".build.yaml"))
	spec := &Spec{}
	err = yaml.Unmarshal(file, spec)
	if err != nil {
		log.Fatal(err)
	}

	// Add commands to install dependencies for the given build type.
	switch spec.Type {
	case "go":
		file := read(filepath.Join(moduleDir, ".gopkgs.json"))
		manifest := &GoManifest{map[string]GoPackage{}, []string{}}
		err = json.Unmarshal(file, &manifest)
		if err != nil {
			log.Fatal(err)
		}
		pkgList := []string{}
		for pkg, _ := range manifest.Packages {
			pkgList = append(pkgList, pkg)
		}
		sort.Strings(pkgList)
		buf.WriteString("RUN git config --global advice.detachedHead false\n\n")
		for _, pkg := range pkgList {
			repo := manifest.Packages[pkg]
			lead := filepath.Dir(pkg)
			name := filepath.Base(pkg)
			fmt.Fprintf(
				buf, `RUN mkdir -p go/src/%s && \
    cd go/src/%s && \
    %s clone %s %s && \
    cd %s && %s %s

`,
				lead, lead, repo.VCS, repo.Src, name, name,
				vcsCheckout[repo.VCS], repo.Rev)
		}
		if len(manifest.Toplevel) > 0 {
			buf.WriteString(`RUN go get -v`)
			for _, imp := range manifest.Toplevel {
				fmt.Fprintf(buf, " \\\n    %s", imp)
			}
			buf.Write([]byte{'\n', '\n'})
		}
	default:
		log.Fatalf(
			"unsupported build type %q specified in the environ/%s.build.yaml file",
			spec.Type, moduleID)
	}

	// Write the module files to a tarfile.
	tbuf := &bytes.Buffer{}
	tarfile := tar.NewWriter(tbuf)
	chdir(rootDir)
	for _, fset := range spec.Files {
		for idx, pat := range fset.Ignore {
			fset.Ignore[idx] = filepath.Join(fset.Src, pat)
		}
		walk(rootDir, fset.Src, fset, tarfile)
	}

	// Write the tarfile to disk.
	hasher := sha256.New()
	err = tarfile.Close()
	if err != nil {
		log.Fatal(err)
	}
	tdata := tbuf.Bytes()
	hasher.Write(tdata)
	tname := fmt.Sprintf("source-%x.tar", hasher.Sum(nil))
	write(filepath.Join(buildDir, tname), tdata)

	// Add the tarfile to the Dockerfile.
	fmt.Fprintf(buf, "ADD %s /module/\n", tname)

	// Write out the build commands.
	for _, cmd := range spec.Commands {
		fmt.Fprintf(buf, "RUN %s\n\n", cmd)
	}
	fmt.Fprintf(buf, "RUN build-module-tarball %s\n", strings.Join(spec.Include, " "))
	buf.WriteString("RUN export-env\n")

	// Write out the new Dockerfile.
	write(filepath.Join(buildDir, "Dockerfile"), buf.Bytes())

	// Create the buildbase image.
	log.Infof("Building the %s/buildbase image", appID)
	chdir(envDir, "buildbase")
	run("docker", "build", "-t", appID+"/buildbase", ".")

	// Create the module image.
	log.Infof("Building the %s/%s.generator image", appID, moduleID)
	chdir(buildDir)
	run("docker", "build", "-t", moduleImage, ".")

	// Create the final image directory.
	err = os.Mkdir(imgDir, 0777)
	if err != nil {
		log.Fatal(err)
	}

	// Copy assets from the module image.
	log.Infof("Copying built assets from %s", moduleImage)
	cid := getOutput("docker", "create", moduleImage) + ":/module/"
	chdir(imgDir)
	run("docker", "cp", cid+"env.json", ".")
	run("docker", "cp", cid+"module.tar", ".")

	// Read the env data.
	envData := read("env.json")
	envKeys := []string{}
	env := map[string]string{}
	err = json.Unmarshal(envData, &env)
	if err != nil {
		log.Fatal(err)
	}
	for key, _ := range env {
		envKeys = append(envKeys, key)
	}
	sort.Strings(envKeys)

	// Write out the dockerfile for the final image.
	buf.Reset()
	buf.WriteString("FROM scratch\nENV ")
	last := len(envKeys) - 1
	for idx, key := range envKeys {
		fmt.Fprintf(buf, "%s=%s", key, env[key])
		if idx == last {
			buf.Write([]byte{'\n'})
		} else {
			buf.WriteString(" \\\n    ")
		}
	}
	buf.WriteString("ADD module.tar /\n")
	switch spec.Type {
	case "go":
		buf.WriteString(`ENTRYPOINT ["/module/bin/run"]`)
	default:
		log.Fatalf(
			"unsupported build type %q specified in the environ/%s.build.yaml file",
			spec.Type, moduleID)
	}
	write(filepath.Join(imgDir, "Dockerfile"), buf.Bytes())

	// Build the final image.
	log.Infof("Building the final %s/%s image", appID, moduleID)
	run("docker", "build", "-t", appID+"/"+moduleID, ".")

}

func chdir(path ...string) {
	err := os.Chdir(filepath.Join(path...))
	if err != nil {
		log.Fatal(err)
	}
}

func getOutput(name string, args ...string) string {
	out, err := exec.Command(name, args...).Output()
	if err != nil {
		log.Fatal(err)
	}
	return strings.TrimSpace(string(out))
}

func read(path string) []byte {
	out, err := ioutil.ReadFile(path)
	if err != nil {
		log.Fatal(err)
	}
	return out
}

func run(name string, args ...string) {
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		log.Fatal(err)
	}
}

func walk(root string, src string, spec *FileSpec, tarfile *tar.Writer) {
	path := filepath.Join(root, src)
	files, err := ioutil.ReadDir(path)
	if err != nil {
		log.Fatal(err)
	}
loop:
	for _, file := range files {
		name := filepath.Join(src, file.Name())
		for _, pat := range spec.Ignore {
			if match, _ := filepath.Match(pat, name); match {
				continue loop
			}
		}
		if file.Mode()&os.ModeSymlink != 0 {
			file, err = os.Stat(name)
			if err != nil {
				log.Fatal(err)
			}
		}
		if file.IsDir() {
			walk(root, name, spec, tarfile)
			continue
		}
		err = tarfile.WriteHeader(&tar.Header{
			Mode:    int64(file.Mode()),
			ModTime: file.ModTime(),
			Name:    filepath.Join(spec.Dst, name),
			Size:    file.Size(),
		})
		if err != nil {
			log.Fatal(err)
		}
		fdata, err := ioutil.ReadFile(name)
		if err != nil {
			log.Fatal(err)
		}
		_, err = tarfile.Write(fdata)
		if err != nil {
			log.Fatal(err)
		}
	}
}

func write(path string, contents []byte) {
	err := ioutil.WriteFile(path, contents, 0644)
	if err != nil {
		log.Fatal(err)
	}
}

func main() {
	if len(os.Args) != 3 {
		fmt.Println("Usage: builder APP_ID MODULE_DIR")
		os.Exit(1)
	}
	build(os.Args[1], os.Args[2])
}
