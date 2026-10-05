# JAZZY-002: Joy timeout後の横方向速度残存

- 対象・基点: JAZZY-001と同じ。JAZZY-001の成功checkpointから独立した変更として進める。
- 観測: 十字左でlinear.y=0.3を受信後、Joyを1.35秒停止してもlinear.y=0.3が残る。
- 原因仮説: timeout処理がlinear.x/angular.zだけをゼロにしている。
- 原因を示す値: 実際のJoy停止時間、ROS購読で観測したTwist、timeout処理の代入先。
- 変更許可: `virtual_joy/rover_gamepad_node.py`のtimeout処理だけ。
- 変更禁止: timeout閾値1.0秒、入力割り当て、速度値、QoS、GUI、shutdown処理。
- 制御環境の合格条件: Joy停止から1.15秒以後の受信Twistでx/y/zすべてゼロ。前進・旋回timeout、入力再開、既存15条件も成功。
- 実対象の合格条件: ユーザーが同一artifactの実利用先で停止を確認。実機未確認なら実機での成功と呼ばない。
- 再現: `tools/verify_jazzy_runtime.py --expected-commit <clean HEAD> --run-dir <ログ先> --state-only --require-lateral-stop`。

