# 原因の確認

実装上、Joy timeoutの代入先はlinear.xとangular.zだけで、linear.yが残っていました。
ROS購読では1.3529秒Joyを止めても[0.0, 0.3, 0.0]のTwistを受信しました。
JAZZY-001で終了処理を修正したcheckpointでも同じ残存を記録しています。

修正はtimeout時のlinear.y=0.0の追加1行だけです。
閾値1.0秒・通常入力の変換・速度値・トピック・終了処理は変更しません。
検証は`--require-lateral-stop --require-clean-shutdown`で、x/y/z停止と先行checkpointの終了・入力変換を確認します。
