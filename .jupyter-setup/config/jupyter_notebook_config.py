c = get_config()
c.ServerApp.ip = '127.0.0.1'
c.ServerApp.port = 8888
c.ServerApp.disable_check_xsrf = True
c.ServerApp.password = 'argon2:$argon2id$v=19$m=10240,t=10,p=8$EXcfHH7mX4GdzG1o6cmNCw$YcVsXSu5W+I7d00qnmtPKz2KsBwLnRD0Kn+oGwLuFng'
