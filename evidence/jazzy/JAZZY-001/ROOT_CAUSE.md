# 原因の確認

未修正のJazzy runでSIGINT後のcontext_ok=Falseを記録しました。
そのcontextへshutdownをもう一度呼ぶと`rcl_shutdown already called`が再現しました。
再現コード・実行PID/hash・出力は`reproduction/root-cause-probe*`と`signal_context_probe.py`を参照。

実装上、roverのfinallyが無条件でshutdownを呼び、両ノードのspinが通常の終了例外を捕捉していませんでした。
GUIはSIGINTによるcontext終了をTk mainloopへ通知していませんでした。

変更はmainの終了処理に限定しました。try_shutdownで二重終了を避け、spinの通常終了例外を捕捉します。
GUIはcontext終了をTkのafterで確認してmainloopを抜けます。
終了時はcontext停止、spin threadの完了、nodeとTkの破棄の順で処理します。
GUIの閉じるcallbackも同じfinallyを通ります。入力値・速度・timeout処理は変更していません。
