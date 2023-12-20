from datetime import datetime
from redis import Redis

r = Redis()


# # v = r.set("dlock", value=1, ex=60, nx=True)
# v = r.setnx("dlock", value=1)
# r.expire("dlock", 60)
#
# if v:
#     print("T: %s, V: %s" % (datetime.now(), v))

lua_scripts = "if redis.call('setnx',KEYS[1],ARGV[1]) == 1 then" + \
            " redis.call('expire',KEYS[1],ARGV[2]) return 1 else return 0 end"
vv = r.eval(lua_scripts, 1, "dis_lock", "v1000", 300)
print("vvv:", vv)
