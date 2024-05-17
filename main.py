from pathlib import Path
import face_recognition
import xattr
import plistlib

PATH = "/img"

def has_finderTag(path):
    # macosのfinderタグがあるか否か, タグの種類は判断してない
    # 一度もタグ付けを指定無いファイルには'com.apple.metadata:_kMDItemUserTags'は存在しないのでtry処理。
    try:
        bplist = xattr.getxattr(path, attr='com.apple.metadata:_kMDItemUserTags')
        if len(plistlib.loads(bplist)) == 0:
            return False
        else:
            return True
    except OSError:
        return False

class Face:
    n = 0
    def __init__(self, image_path):
        self.name = self.get_alphabet()
        self.load_image = face_recognition.load_image_file(image_path)
        self.face_encodes = face_recognition.face_encodings(self.load_image)
        Face.n += 1

    @classmethod
    def get_alphabet(cls):
        # インスタンスを生成するたびに識別用のアルファベットを生成する。
        alphabet_index = cls.n % 26  # 26はアルファベットの数
        alphabet = chr(ord('A') + alphabet_index)
        return alphabet

if __name__ == "__main__":
    all_imgs = list(Path(PATH).expanduser().resolve().glob('**/*.JPG'))
    # 照合元の画像リスト
    verification_imgs = list(filter(has_finderTag, all_imgs))
    print(verification_imgs)
    verification_faces = [Face(i) for i in verification_imgs]
    verification_encode_faces = [i.face_encodes[0] for i in verification_faces]

    for img in all_imgs:
        # 顔照合
        # うまく処理がいかないファイルは後で手動でリネームするのでなにもしないことにした。
        target_encode_face = Face(img).face_encodes
        # 照合不可の場合代わりにNF(NotFound)を代入
        if len(target_encode_face) == 0:
            alphabet_name = ""
        # 一人以上見つかった場合は　PP(Peaple)
        elif len(target_encode_face) > 1:
            alphabet_name = ""
        else:
            result = face_recognition.face_distance(verification_encode_faces, target_encode_face[0]).tolist() #numpyArrayなので最後リストに変換
            result_index = result.index(min(result)) #一番数値の低い数値のリストインデックスを取得
            alphabet_name = verification_faces[result_index].name+'_'#識別アルファベット名取得

        print(f"{img.name} => {alphabet_name}")

        # rename
        img.rename(img.parent/Path(f"{alphabet_name}{img.name}"))
        # 同じ名前のRAWデータがあれば一緒にリネーム
        raw = img.with_suffix('.CR2')
        if raw.exists():
            raw.rename(raw.parent/Path(f"{alphabet_name}{raw.name}"))
