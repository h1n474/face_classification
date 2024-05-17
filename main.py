import face_recognition
import math
import plistlib
from PIL import Image
from pathlib import Path
import xattr

PATH = "/img"

class Faces:
    n = 0
    def __init__(self, img_path):
        self.name = self.get_alphabet()
        self.img_path = img_path
        self.load_image = face_recognition.load_image_file(self.img_path)
        self._encodes = self._get_encodings()
        Faces.n += 1

        if len(self._encodes) == 1:
            self.encode = self._encodes[0]
        else:
            locations = self._get_locations()
            locations_point = list(map(self._get_center_coordinates, locations))
            locations_distance = list(map(self._get_distance_between_ImgcenterToPoint, locations_point))
            dr_index = locations_distance.index(min(locations_distance))
            self.encode = self._encodes[dr_index]

    def _get_encodings(self)-> list:
        return face_recognition.face_encodings(self.load_image)

    def _get_locations(self)-> list:
        return face_recognition.face_locations(self.load_image)

    def _get_center_coordinates(self, box:(float, float, float, float))-> (float, float):
        top, right, bottom, left = box
        x = (left + right) / 2
        y = (top + bottom) / 2
        return (x, y)

    def _get_distance_between_ImgcenterToPoint(self, point:(float,float) )-> float:
        with Image.open(self.img_path) as img:
            img_x = img.size[0]/2
            img_y = img.size[1]/2
        return math.sqrt((point[0] - img_x)**2 + (point[1] - img_y)**2)

    @classmethod
    def get_alphabet(cls):
        #インスタンスを生成するたびに識別用のアルファベットを生成する。
        alphabet_index = cls.n % 26  #26はアルファベットの数
        alphabet = chr(ord('A') + alphabet_index)
        return alphabet


#macos_finderのラベルがあるかどうか判断する
def has_finderTag(path):
    #macosのfinderタグがあるか否か, タグの種類は判断してない
    #一度もタグ付けを指定無いファイルには'com.apple.metadata:_kMDItemUserTags'は存在しないのでtry処理。
    try:
        bplist = xattr.getxattr(path, attr='com.apple.metadata:_kMDItemUserTags')
        if len(plistlib.loads(bplist)) == 0:
            return False
        else:
            return True
    except OSError:
        return False


if __name__ == '__main__':
    #照合するリストを作成する。
    all_imgs = list(Path().glob('**/*.JPG'))
    label_imgs = list(filter(has_finderTag, all_imgs))
    src_faces = [Faces(i) for i in label_imgs]
    src_faces_encode = [i.encode for i in src_faces]

    for img in all_imgs:
        #照合
        try:
            dst_encode = Faces(img).encode
            result = face_recognition.face_distance(src_faces_encode, dst_encode).tolist() #numpyArrayなので最後リストに変換
            result_index = result.index(min(result)) #一番数値の低い数値のリストインデックスを取得

            alphabet_name = src_faces[result_index].name+'_'#識別アルファベット名取得
        except:
            alphabet_name = ""
        print(f"{img.name} => {alphabet_name}")

        #リネーム
        img.rename(img.parent/Path(f"{alphabet_name}{img.name}"))
        #同じ名前のRAWデータがあれば一緒にリネーム
        raw = img.with_suffix('.CR2')
        if raw.exists():
            raw.rename(raw.parent/Path(f"{alphabet_name}{raw.name}"))
