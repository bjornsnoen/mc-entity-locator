#!/usr/bin/env python

import anvil
import glob
from nbt import nbt
import argparse
from typing import List, Dict
from dataclasses import dataclass, fields
from pathlib import Path
from math import floor
from tqdm import tqdm

EntityList = List[nbt.TAG_Compound]

@dataclass
class Point2d:
    x: int
    z: int

@dataclass
class Point:
    x: int
    y: int
    z: int

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, int):
                setattr(self, field.name, field.type(value))

    def string_array(self):
        return [str(self.x), str(self.y), str(self.z)]
    
    def chunk(self) -> Point2d:
        chunkX = floor(int(self.x) / 16)
        chunkZ = floor(int(self.z) / 16)
        return Point2d(chunkX, chunkZ)

    def region(self) -> Point2d:
        regionX = floor(self.chunk().x / 32)
        regionZ = floor(self.chunk().z / 32)
        return Point2d(regionX, regionZ)
    
CoordinateList = List[Point]
BlockMap = Dict[str, CoordinateList]

class BlockFinder:
    def __init__(self, world: str, output_file: str):
        self.world = world.rstrip('/')
        output_path = Path(output_file)
        
        if output_path.exists() and not output_path.is_file:
            raise Exception('The specified output file exists and cannot be overwritten')
        elif output_path.exists() and output_path.is_file():
            output_path.unlink()
        
        output_path.touch()
        #with output_path.open(mode='a') as fp:
        #    fp.writelines(['x,y,z\n'])

        self.output_path = output_path

    def get_level(self, chunk: nbt.NBTFile) -> nbt.TAG_Compound:
        for tag in chunk.tags:
            if tag.name == "Level":
                return tag
        return None
    
    def get_entities(self, level: nbt.TAG_Compound) -> EntityList:
        my_list = []

        try:
            my_list = my_list + level['TileTicks'].tags
        except:
            pass

        try:
            my_list = my_list + level['TileEntities'].tags
        except:
            pass
        
        try:
            my_list = my_list + level['Entities'].tags
        except:
            pass

        return my_list


    def test_chunk(self, chunk: nbt.NBTFile, block_id: str) -> CoordinateList:
        if block_id.find(':') != -1:
            potential_values = [block_id, block_id.split(':')[1]]
        else:
            potential_values = [block_id]

        level = self.get_level(chunk)
        if not level:
            return False

        entities = self.get_entities(level)
        if not entities:
            return False
        
        positions = []

        for entity in entities:
            # Try plain tag search
            try:
                if entity['id'].value in potential_values:
                    positions.append(self.get_position(entity))
                    continue
                elif entity['id'].value == 'minecraft:item':
                    item = entity['Item']
                    if item['id'].value in potential_values:
                        positions.append(self.get_position(item))
                        continue
                elif entity['id'].value == 'minecraft:item_frame':
                    item = entity['Item']
                    if item['id'].value in potential_values:
                        positions.append(self.get_position(entity))
                        continue
            except:
                pass
            
        return positions
    
    def get_position(self, something: nbt.TAG_Compound) -> Point:
        coords = list(filter(lambda tag: tag.name in ['x', 'y', 'z'], something.tags))
        if coords:
            point = Point(coords[0].value, coords[1].value, coords[2].value)
        else:
            pos = something['Pos']
            point = Point(pos[0].value, pos[1].value, pos[2].value)
        
        return point

    def find(self, block_id: str):
        path = Path(self.world)
        if path.is_file():
            files = [self.world]
        elif path.is_dir():
            files = glob.glob(self.world + "/*")
        else:
            raise Exception("Not a valid world region path")

        progressBar = tqdm(files)

        for file in progressBar:
            progressBar.set_description("Processing fragment {file}".format(file=file.split('/')[-1]))
            region = anvil.Region.from_file(file)
            for x in range(32):
                for y in range(32):
                    chunk = region.chunk_data(x, y)
                    if chunk is not None:
                        coordinate_list = self.test_chunk(chunk, block_id)
                        if coordinate_list:
                            rows = list(map(lambda coordinate: [str(coordinate.region().x), str(coordinate.region().z), str(x), str(y)], coordinate_list))
                            self.output(rows)
    
    def output(self, rows: List):
        with self.output_path.open(mode='a') as fp:
            stringified = list(map(lambda row: ';'.join(row) + "\n", rows))
            fp.writelines(stringified)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find stuff in the world.')
    parser.add_argument('world', type=str, help='World region directory')
    parser.add_argument('block', type=str, help='The block id you want to eradicate (like minecraft:Chest)')

    args = parser.parse_args()

    finder = BlockFinder(args.world, "out/" + args.block + ".csv")
    finder.find(args.block)
