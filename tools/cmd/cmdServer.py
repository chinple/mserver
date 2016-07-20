'''

@author: chinple
'''
from BaseHTTPServer import BaseHTTPRequestHandler
import BaseHTTPServer
import subprocess

class CmdServerhandler(BaseHTTPRequestHandler):
    def do_POST(self):
        cmd = self.rfile.read(int(self.headers['Content-Length']))
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmdres, cmderr = proc.communicate()
            returncode = proc.returncode
            resp = {'code':returncode, 'res':cmdres, 'err':cmderr}
            resp = str(resp)
        except :
            resp = "Fail to execute: %s" % cmd
        try:
            self.send_response(200)
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        finally:
            self.close_connection = 1

if __name__ == "__main__":
    BaseHTTPServer.test(CmdServerhandler, BaseHTTPServer.HTTPServer)
