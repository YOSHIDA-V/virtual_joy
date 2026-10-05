# JAZZY-001: SIGINT終了時の例外

- 対象: Ubuntu 24.04 / ROS 2 Jazzy / CycloneDDS / ROS_DOMAIN_ID=100。
- 基点: Humble版main `ab3a96f49c4a5e7c17e6e21d49673487c2fecfe6`。
- 観測: READMEのrover launchへSIGINTを送ると、ExternalShutdownException、KeyboardInterrupt、二重shutdownのRCLErrorが出る。
- 原因仮説: Jazzyのsignal handlerによるcontext終了をspinと後処理が通常の終了として扱っていない。
- 原因を示す値: 起動した実体のhash、終了ログのstack、終了済みcontextへshutdownを呼んだ場合の例外。
- 変更許可: `virtual_joy/virtual_joy_node.py`と`virtual_joy/rover_gamepad_node.py`のmainと必要なimportだけ。
- 変更禁止: GUI、入力割り当て、速度値、タイムアウト値、QoS、launchのトピック。
- 制御環境の合格条件: 起動・通信後にlaunch parentへSIGINTを1回送り、両ノードが正常終了する。tracebackなし、起動した子PIDの残存なし。
- 回帰条件: Joy >=10Hz、Twist >=50Hz、8軸13ボタン、既存の入力変換15条件。
- 実対象の合格条件: ユーザー画面で同一artifactの手動GUI操作・終了を確認。未確認ならmainへ昇格しない。
- 再現: `tools/verify_jazzy_runtime.py --expected-commit <clean HEAD> --run-dir <ログ先> --require-clean-shutdown`。詳細の環境と実行値は各manifest。

