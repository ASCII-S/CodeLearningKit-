c = get_config()
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.disable_check_xsrf = True
c.ServerApp.password = 'argon2:$argon2id$v=19$m=10240,t=10,p=8$eeDc/02U32m+5JDhbDHypg$mvBdxb2rxtKw22lWl9F0Xmv26Lc9JgVeftPbpEv6WqE'
c.ServerApp.browser = '/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
