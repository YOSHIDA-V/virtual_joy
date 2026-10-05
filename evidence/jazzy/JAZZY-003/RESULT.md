# 制御環境での結果

- 状態: FIXED_IN_CONTROLLED_ENVIRONMENT。push後はPUSHED_CANDIDATE。ユーザー環境での新規導入は未確認。
- 実行commit: `8513fc77e1c1cce57ae087ca2cbb788bf35d55af`。clean checkout、導入済みartifactとソースのhash一致を確認。
- Ubuntu 24.04 / ROS 2 Jazzyでrosdep check、rosdep install、colcon buildがexit 0。
- virtual_joy_node / rover_gamepad_nodeの両entrypoint、Joy-only / rover launchの引数一覧を確認。
- 既存UI geometry単体テスト5件がPASS。
- CycloneDDS / ドメイン100で同一runtimeの19条件がPASS。Joy実測19.9945Hz、Twist実測100.2224Hz。
- 横方向timeoutで[0, 0, 0]を受信し、SIGINTで両ノードが正常終了。終了修正とtimeout修正の回帰なし。
- 実行PID・cwd・コマンド・commit/package hash・exit codeは`qualification/installation-manifest.json`、runtimeは同フォルダーのmanifestとresultを参照。
- GUIの手動操作・実機・新規のユーザー環境での導入は未確認。mainへの昇格は行わない。
