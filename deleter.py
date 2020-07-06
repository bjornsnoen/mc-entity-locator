#!/usr/bin/env python

from os import getcwd, chdir
from subprocess import run
from tqdm import tqdm
import argparse
from pathlib import Path
from glob import glob
from typing import List

StringList = List[str]

class Orchestrator:
    def __init__(self, world: str, mcaselector_dir: str):
        self.javabin = self.run_supbroc(["which", "java"], True)
        if not (self.javabin):
            raise Exception("No java bin found, you need java for this")
        
        self.world_path = Path(world)
        if not self.world_path.exists():
            raise Exception("No such world {world}".format(world=world))

        self.mcaselector_dir = Path(mcaselector_dir.rstrip("/"))
        if not self.mcaselector_dir.exists() or not self.mcaselector_dir.is_dir():
            raise Exception("You gotta provide a path to the directory where mcaselector is installed")

        self.mcaselector = self.mcaselector_dir / "build/libs/mcaselector-1.12-all.jar"
        if not self.mcaselector.exists():
            gradle = self.mcaselector_dir / "gradlew"
            iwd = getcwd()
            chdir(str(self.mcaselector_dir.resolve()))

            print("compiling mcaselector...")
            self.run_supbroc([str(gradle.resolve()), "minifyCss", "shadowJar"])
            print("Done")

            chdir(iwd)
        
    def run_supbroc(self, command: StringList, capture: bool = False):
        complete = run(command, capture_output=capture)
        if capture:
            return complete.stdout.strip().decode()
    
    def get_csv_files(self):
        me = Path(__file__)
        directory = me.parent
        out_directory = directory / "out"
        csvs = glob(str(out_directory.resolve() / "*.csv"))
        return csvs
    
    def go_ham(self):
        files = self.get_csv_files()
        longest = 0
        for file in files:
            path = Path(file)
            length_of_name = len(path.stem)
            longest = max(length_of_name, longest)

        progressBar = tqdm(files)
        for file in progressBar:
            path = Path(file)
            command = [
                str(self.javabin),
                "-jar",
                str(self.mcaselector.resolve()),
                "--headless",
                "--mode",
                "deleteBlock",
                "--world",
                str(self.world_path.resolve()),
                "--csv",
                file,
                "--block-id",
                path.stem
            ]
            progressBar.set_description("{block:_>{longest}}".format(longest=longest, block=path.stem))

            self.run_supbroc(command, True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Delete stuff using mcaselector')
    parser.add_argument('world', type=str, help='World region directory')
    parser.add_argument('mcaselector', type=str, help='Path to mcaselector installation')

    args = parser.parse_args()

    orchestrator = Orchestrator(args.world, args.mcaselector)
    orchestrator.go_ham()
