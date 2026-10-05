# 制御環境での結果

- 状態: FIXED_IN_CONTROLLED_ENVIRONMENT。push後はPUSHED_CANDIDATE。ユーザーの実利用環境は未確認。
- 実行commit: `b61ca82a13b8478c18d1fa6eabf9406f09872fa1`。clean checkout・導入済みmodule/launch/manifestとソースのhash一致を実行前後に確認。
- 環境: Ubuntu 24.04 / ROS 2 Jazzy / CycloneDDS / ドメイン100 / LOCALHOST / 専用トピック・Xvfb。
- 同じ再現条件でSIGINT終了を再実行: 両ノードがexit 0、tracebackなし、起動した子PIDの残存なし。
- Joy: 80件/4.000967秒 = 19.9952Hz。Twist: 400件 = 99.9758Hz。
- 入力・timeout・再開の18条件がPASS。横方向timeoutはJAZZY-002の診断として残り、ここでは修正していない。
- Tkの登録済みclose callbackをプログラムから呼び、GUI mainの正常return・exit 0・tracebackなしを確認。ユーザーのマウス入力は合成していない。
- ログ・PID・引数・runtime hash・測定値は`qualification/`を参照。
- 手動GUI操作、WSLgのユーザー画面、実機、異なるRMW間通信は未確認。mainへの昇格は行わない。
