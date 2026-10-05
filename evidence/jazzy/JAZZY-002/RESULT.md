# 制御環境での結果

- 状態: FIXED_IN_CONTROLLED_ENVIRONMENT。push後はPUSHED_CANDIDATE。実機は未確認。
- 実行commit: `5982018f2008d7a8972f26788e64d4eaf55fd4ef`。clean checkout、導入済みartifactとソースのhash一致を確認。
- 環境: Ubuntu 24.04 / ROS 2 Jazzy / CycloneDDS / ドメイン100 / LOCALHOST / 専用トピック・Xvfb。
- Joy停止から1.15秒以後の受信Twistはx/y/zすべて0。前進・横移動・旋回timeout、入力再開を含む19条件がPASS。
- Joy実測19.9932Hz、Twist実測100.2160Hz。各件数と測定時間は`qualification/runtime-result.json`。
- SIGINT終了の回帰確認: 両ノードが正常終了、例外なし、起動した子PIDの残存なし。
- 停止閾値1.0秒、通常の入力・速度値は変更していない。
- 手動GUI・実機・ユーザーの実利用先での確認は未実施。mainへ昇格しない。
