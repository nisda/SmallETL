from typing import List, Dict



def confirm_continue(
        message:List[str]|str = "処理を続行しますか？",
        prompt:str = "$ OK:[Enter] / 中止:[CTRL+C] > ",
    ) -> bool:
    # リスト化
    messags = message if isinstance(message, list) else [message]

    # メッセージ表示
    print()
    print("\n".join(messags))
    print()

    # 確認
    ret = input(prompt)

    # 終了
    return True




def choice(
        choices:List[Dict],
        message:str="選択してください。",
        list_format:str=None, # 未指定時はカンマ区切り
    ):

    if list_format is None:
        captions:List[str] = [
            ",".join([ str(v) for v in c])
            for c in choices
        ]
    else:
        captions:List[str] = [
            list_format.format(**c)
            for c in choices
        ]


    count = len(choices)
    def __disp():
        print()
        print(message)
        width = len(str(count))
        for i, caption in enumerate(captions):
            print(f"  {str(i).rjust(width, " ")}: {caption}")
        print()

    attempts_count: int = 0
    while True:
        # ５回に１回は選択肢を表示
        if attempts_count == 0:
            __disp()
        attempts_count = (attempts_count + 1) % 5

        input_num = input(f"$ prease enter [ 0 - {count-1} ] > ")
        try:
            num:int = int(input_num)
            if 0 <= num and num < count:
                return choices[num]
        except Exception as e:
            pass

