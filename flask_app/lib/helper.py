import cv2
import supervision as sv
from inference.models.utils import get_roboflow_model
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.meld import Meld
from collections import defaultdict
from mahjong.shanten import Shanten
import os
from inference_sdk import InferenceHTTPClient, InferenceConfiguration

class MahjongInference:
    def __init__(self, api_key, model_id, test_image_dir=None):
        self.test_image_dir = test_image_dir
        self.api_key = api_key
        self.model_id = model_id
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        if test_image_dir:
            self.image_files = self.get_image_files_from_directory(test_image_dir)

        self.CLIENT = InferenceHTTPClient(
            api_url="https://detect.roboflow.com",
            api_key=self.api_key
        )
        self.custom_configuration = InferenceConfiguration(confidence_threshold=0.5, max_detections=14)
        self.CLIENT.configure(self.custom_configuration)
        # self.result = None

    def infer(self):
        return self.CLIENT.infer(self.image_files, model_id=self.model_id)

    def infer_single_image(self, image_path):
        return self.CLIENT.infer([image_path], model_id=self.model_id)
    
    def infer_directory(self, directory_path):
        image_files = self.get_image_files_from_directory(directory_path)
        return self.CLIENT.infer(image_files, model_id=self.model_id)

    def get_image_files_from_directory(self, directory_path):
        files_in_directory = os.listdir(directory_path)
        return [os.path.join(directory_path, file) for file in files_in_directory if os.path.splitext(file)[1].lower() in self.image_extensions and "annotated" not in file]
    
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.meld import Meld
from collections import defaultdict
from mahjong.shanten import Shanten


class MahjongScorer:
    def __init__(self, player_wind='east', round_wind='east'):
        self.calculator = HandCalculator()
        self.config = HandConfig(is_tsumo=False, is_riichi=False,
                                 player_wind=player_wind, round_wind=round_wind)
        self.dora_indicators = []

    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def update_dora_indicators(self, dora_indicators):
        self.dora_indicators = dora_indicators

    def _parse_hand_tiles(self, hand):
        hand_dict = defaultdict(list)
        for tile in hand:
            if 'm' in tile:
                hand_dict['m'].append(tile[0])
            elif 'p' in tile:
                hand_dict['p'].append(tile[0])
            elif 's' in tile:
                hand_dict['s'].append(tile[0])
            elif 'z' in tile:
                hand_dict['z'].append(tile[0])

        sorted_hand = ''
        for suit in 'mpsz':
            if suit in hand_dict:
                sorted_tiles = ''.join(sorted(hand_dict[suit]))
                sorted_hand += f'{sorted_tiles}{suit}'
        return sorted_hand

    def _convert_hand_to_tiles(self, hand, tiles_type):
        hand_string = self._parse_hand_tiles(hand)
        if tiles_type == 136:
            return TilesConverter.one_line_string_to_136_array(string=hand_string)
        else:
            return TilesConverter.one_line_string_to_34_array(string=hand_string)

    def _tile_string_representation(self, hand):
        return self._parse_hand_tiles(hand)

    def _calculate_dora_tiles(self):
        return TilesConverter.one_line_string_to_136_array(string="".join(self.dora_indicators))

    def _print_verbose(self, hand, result):
        print("你的手牌是: ", self._tile_string_representation(hand))
        print(f"点数: {result.cost['total']}, 番数: {result.han}, 符数: {result.fu}, 牌型: {result.yaku}, 满吗: {result.cost['yaku_level']}")
        for yaku in result.yaku:
                print(f"\t\t役: {yaku.name}, 役数: {yaku.han_closed}")
        for fu_item in result.fu_details:
            print(fu_item)
        print(f"Congrats!\n")

    def hand_score(self, hand, win_tile, verbose=True):
        tiles = self._convert_hand_to_tiles(hand, tiles_type=136)
        parsed_win_tile = self._convert_hand_to_tiles([win_tile], tiles_type=136)[0]
        dora_tiles = self._calculate_dora_tiles()
        result = self.calculator.estimate_hand_value(tiles, parsed_win_tile,
                                                     config=self.config, dora_indicators=dora_tiles)
        if not result.error:
            if verbose:
                self._print_verbose(hand, result)
            return result.cost['total'], result
        else:
            if verbose:
                print("ERROR:", result.error)
            return -1, None

    def calculate_shanten(self, hand):
        tiles = self._convert_hand_to_tiles(hand, tiles_type=34)
        shanten_calculator = Shanten()
        return shanten_calculator.calculate_shanten(tiles)

    def _generate_full_tile_set(self):
        numbered_tiles = [f"{num}{suit}" for suit in "mps" for num in range(1, 10)]
        honor_tiles = [f"{num}z" for num in range(1, 8)] # Only 1z through 7z exist
        return numbered_tiles + honor_tiles

    def calculate_tenpai_tiles(self, hand):
        full_tile_set = self._generate_full_tile_set()
        winning_tiles = []
        for tile in full_tile_set:
            score, result = self.hand_score(hand + [tile], win_tile=tile, verbose=False)
            if score != -1:
                winning_tiles.append((score, tile, result))
        return sorted(winning_tiles, key=lambda k: k[0], reverse=True)
    
    def print_possible_wins(self, winning_tiles):
        if not winning_tiles:
            print("\t\t无役 别搞了!")
            return
        for score, tile, result in winning_tiles:
            print(f"\t\t{'自摸' if self.config.is_tsumo else '荣和'}: {tile}, 点数: {result.cost['total']}, 番数: {result.han}, 符数: {result.fu}, 牌型: {result.yaku}, 满吗: {result.cost['yaku_level']}")
            for yaku in result.yaku:
                print(f"\t\t\t役: {yaku.name}, 役数: {yaku.han_open if yaku.han_open else yaku.han_closed}")
            for fu_item in result.fu_details:
                print("\t\t\t", fu_item)

    def list_all_possible_wins(self, hand):
        print("听牌! 你的手牌是: ", self._parse_hand_tiles(hand))
        config_scenarios = [
            (False, False, "\t如果默听荣和"),
            (True, False, "\t如果自摸"),
            (False, True, "\t如果立直荣和"),
            (True, True, "\t如果立直自摸")
        ]

        original_config = (self.config.is_tsumo, self.config.is_riichi)
        for is_tsumo, is_riichi, scenario_message in config_scenarios:
            self.update_config(is_tsumo=is_tsumo, is_riichi=is_riichi)
            winning_tiles = self.calculate_tenpai_tiles(hand)
            print(scenario_message)
            self.print_possible_wins(winning_tiles)

        self.update_config(is_tsumo=original_config[0], is_riichi=original_config[1])
        print("GLHF\n")
        
    def process_hand(self, hand, win_tile=None, dora_indicators=None):
        if dora_indicators is not None:
            self.update_dora_indicators(dora_indicators)

        if len(hand) == 14:
            self.hand_score(hand, win_tile)
        elif len(hand) == 13:
            shanten = self.calculate_shanten(hand)
            if shanten == 0:
                self.list_all_possible_wins(hand)
            else:
                print(f"Shanten: {shanten}")
        else:
            print("Invalid hand length")
    
class ImageProcessor:
    def __init__(self, image_files, result):
        self.image_files = image_files
        self.result = result
        self.mahJongScorer = MahjongScorer()

    def get_scale_factor(self, image_size, reference_size=800, base_scale=0.8, base_thickness=2):
        # Calculate the scale factor based on the image size compared to a reference size
        scale_factor = max(image_size) / reference_size
        scaled_text_scale = max(base_scale * scale_factor, base_scale)  # Ensure minimum scale
        scaled_text_thickness = max(int(base_thickness * scale_factor), base_thickness)  # Ensure minimum thickness
        return scaled_text_scale, scaled_text_thickness

    def process_images(self):
        for img, resp in zip(self.image_files, self.result):
            image = cv2.imread(img)
            # Get scale and thickness based on image size
            text_scale, text_thickness = self.get_scale_factor(image.shape[:2])

            detections = sv.Detections.from_inference(resp)
            bounding_box_annotator = sv.BoundingBoxAnnotator(thickness=text_thickness)
            label_annotator = sv.LabelAnnotator(text_scale=text_scale, text_thickness=text_thickness)
            # conf_annotator = sv.PercentageBarAnnotator()

            annotated_image = bounding_box_annotator.annotate(scene=image, detections=detections)
            annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections)
            # annotated_image = conf_annotator.annotate(scene=annotated_image, detections=detections)
            sv.plot_image(annotated_image)
            hand = sorted([pred['class'] for pred in resp['predictions']], key=lambda x: (x[1], x[0]))
            print(img, hand, len(hand))
            self.mahJongScorer.process_hand(hand, hand[0], [])
            # except Exception as e:
            #     print("Cannot score hand or calculaute shanten", e)

if __name__ == "__main__":
    api_key = "YOUR_API_KEY"
    model_id = "YOUR_MODEL_ID"
    test_image_dir = "/path/to/test/images"
    
    inference = MahjongInference(api_key, model_id, test_image_dir)
    result = inference.infer()
    
    image_files = inference.get_image_files_from_directory(test_image_dir)
    
    processor = ImageProcessor(image_files, result)
    processor.process_images()
    
