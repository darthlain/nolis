# nolis
pythonで作ったlispっぽいもの 作りかけ

プリミティブ
(let a b) # 現在の環境に変数登録 lispのletとは何の関係もない
(set a b) # 名前検索して発見した最も内側の環境の変数を書き換える
(def f () ...) # (let f (fn () ...)) の言い換え
(fn () ...) # lambda 新しい環境を作る
(do ...) # begin
(quote it) # itは文字列になる
(import it :from . :as .)
(if 1 2 3 4 5)

# -> でメソッド参照
((-> "hello {}" format) "world")

# 関数部分に数や文字列を入れると添字参照になる スライスも使える
(let a (list (range 1 6)))
(3 a)
(1:4 a)

# 参照はsetの左部分にあれば代入できる
(set (2 a) 13)

# += -= 等は一通り使える

# 追加したいプリミティブ and or for(clのloopみたいに)

関数
# + - % = == is 等
# setは被ってしまったのでSetでアクセスできる
# evalはとりあえずeval_という名前に

トリビア
(= "hello" 'hello)
(functools.reduce + '(1 2 3 4 5))
