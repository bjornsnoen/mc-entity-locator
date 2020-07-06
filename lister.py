#!/usr/bin/env python

import argparse
import glob
import anvil
import re
from nbt import nbt
from finder import BlockFinder, BlockMap, Point
from pathlib import Path
from tqdm import tqdm
from typing import Dict, List

class InvalidFinder(BlockFinder):
    def __init__(self, world: str):
        self.world = world.rstrip('/')
        self.matcher = re.compile(r"[a-z0-9/._\-:]+")
    

    def get_invalid_entities_in_chunk(self, chunk: nbt.NBTFile) -> BlockMap:
        level = self.get_level(chunk)
        if not level:
            return {}

        entities = self.get_entities(level)
        if not entities:
            return {}

        positions = {}
        def put_to_positions(block_id: str, position: Point):
            if block_id not in positions.keys():
                positions[block_id] = []
            positions[block_id].append(position)

        for entity in entities:
            # Try plain tag search
            try:
                pos = self.get_position(entity)
                if pos.x == -55 and pos.y == 47 and pos.z == 425:
                    a = 1
                    pass
                if not self.matcher.fullmatch(entity['id'].value):
                    put_to_positions(entity['id'].value, self.get_position(entity))
                    continue
                elif entity['id'].value == 'minecraft:item':
                    item = entity['Item']
                    if not self.matcher.fullmatch(item['id'].value):
                        put_to_positions(item['id'].value, self.get_position(entity))
                        continue
                elif entity['id'].value == 'minecraft:item_frame':
                    item = entity['Item']
                    if not self.matcher.fullmatch(item['id'].value):
                        put_to_positions('minecraft:item_frame', self.get_position(entity))
                        continue
                elif entity['id'].value == 'minecraft:chest' or entity['id'].value == 'minecraft:shulker_box':
                    items = entity['Items']

                    for item in items:
                        if not self.matcher.fullmatch(item['id'].value):
                            put_to_positions(item['id'].value, self.get_position(entity))
                            continue

            except:
                pass

        return positions

    def find(self):
        path = Path(self.world)
        if path.is_file():
            files = [self.world]
        elif path.is_dir():
            files = glob.glob(self.world + "/*")
        else:
            raise Exception("Not a valid world region path")

        progressBar = tqdm(files)
        mcaselector_csv_files = {}

        for file in progressBar:
            progressBar.set_description("Processing fragment {file}".format(file=file.split('/')[-1]))
            region = anvil.Region.from_file(file)
            for x in range(32):
                for y in range(32):
                    chunk = region.chunk_data(x, y)
                    if chunk is not None:
                        block_map = self.get_invalid_entities_in_chunk(chunk)
                        for block_id, coordinates in block_map.items():
                            if block_id not in mcaselector_csv_files.keys():
                                mcaselector_csv_files[block_id] = []
                            
                            mcaselector_csv_files[block_id] += list(map(lambda coordinate: [str(coordinate.region().x), str(coordinate.region().z), str(x), str(y)], coordinates))

        self.output(mcaselector_csv_files)

    def output(self, block_map: Dict[str, List]):
        for block_id, coordinates in block_map.items():
            output = Path(__file__).parent.resolve() / "out/{block_id}.csv".format(block_id=block_id)
            with output.open(mode='a') as fp:
                stringified = list(map(lambda coordinate: ';'.join(coordinate) + "\n", coordinates))
                fp.writelines(stringified)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='List invalid stuff in the world')
    parser.add_argument('world', type=str, help='World region directory')

    args = parser.parse_args()

    finder = InvalidFinder(args.world)
    finder.find()
