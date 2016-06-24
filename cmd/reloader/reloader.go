// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"syscall"
	"time"

	"github.com/fsnotify/fsevents"
	"github.com/tav/golly/process"
)

var running *exec.Cmd

var (
	kill   = &sync.Mutex{}
	killed = false
	mutex  = &sync.Mutex{}
	wg     = &sync.WaitGroup{}
)

func killProcess() {
	mutex.Lock()
	if running != nil {
		kill.Lock()
		killed = true
		kill.Unlock()
		pgid, err := syscall.Getpgid(running.Process.Pid)
		if err != nil {
			fmt.Printf("ERROR: failed to get the pgid for the 'go run' process: %s\n", err)
			os.Exit(1)
		}
		syscall.Kill(-pgid, 15)
		if err != nil {
			fmt.Printf("ERROR: failed to kill the 'go run' process: %s\n", err)
			os.Exit(1)
		}
		mutex.Unlock()
		wg.Wait()
		kill.Lock()
		killed = false
		kill.Unlock()
	} else {
		mutex.Unlock()
	}
}

func run() {
	killProcess()
	fmt.Println("\n------------------------- BUILDING AND RUNNING APP -------------------------\n")
	cmd := exec.Command("go", "run", "app/app.go", "app/handlers.go")
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	if err := cmd.Start(); err != nil {
		fmt.Printf("\nERROR: %s\n", err)
		return
	}
	running = cmd
	wg.Add(1)
	go func() {
		err := cmd.Wait()
		if err != nil {
			kill.Lock()
			if !killed {
				fmt.Printf("\n!! %s\n", err)
			}
			kill.Unlock()
		}
		mutex.Lock()
		running = nil
		mutex.Unlock()
		wg.Done()
	}()
}

func main() {
	cwd, err := os.Getwd()
	if err != nil {
		log.Fatal(err)
	}
	watcher := &fsevents.EventStream{
		Paths:   []string{filepath.Join(cwd, "app")},
		Latency: 50 * time.Millisecond,
		Flags:   fsevents.FileEvents | fsevents.WatchRoot,
	}
	watcher.Start()
	process.SetExitHandler(killProcess)
	for {
		run()
		<-watcher.Events
	}
}
