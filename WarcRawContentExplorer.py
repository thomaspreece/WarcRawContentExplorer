#!/usr/bin/env python

"""Simple HTTP Server With Upload.
This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.
"""

__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]
__author__ = "bones7456"
__home_page__ = "http://li2z.cn/"

import os
import cgi
import posixpath

try:
    # Python 2
    import BaseHTTPServer
except ImportError:
    # Python 3
    import http.server as BaseHTTPServer


import urllib
import cgi
import sys

import shutil
import mimetypes
import re
import cgi
import webbrowser
import base64

from warcio.archiveiterator import ArchiveIterator
from warcio.recordloader import ArchiveLoadFailed

try:
    # Python 2
    from urlparse import urlparse, parse_qs
    from urllib import unquote
    from urllib import quote
except ImportError:
    # Python 3
    from urllib.parse import urlparse, parse_qs
    from urllib.parse import unquote
    from urllib.parse import quote

try:
    # Python 2
    use_bytes_io=False
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO, BytesIO
    use_bytes_io=True



class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET/HEAD/POST commands.
    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.
    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.
    """

    server_version = "SimpleHTTPWithUpload/" + __version__

    # Python 3 Compatability Function
    def write_webpage(self, stringIOHandle):
        if(use_bytes_io == True):
            raw_string = stringIOHandle.read()
            stringIOHandle.close()
            bytesIOHandle = BytesIO(raw_string.encode())
            self.copyfile(bytesIOHandle, self.wfile)
        else:
            self.copyfile(stringIOHandle, self.wfile)

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.write_webpage(f)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print(r, info, "by: ", self.client_address)
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Upload Result Page</title>\n")
        f.write("<body>\n<h2>Upload Result Page</h2>\n")
        f.write("<hr>\n")
        if r:
            f.write("<strong>Success:</strong>")
        else:
            f.write("<strong>Failed:</strong>")
        f.write(info)
        f.write("<br><a href=\"%s\">back</a>" % self.headers['referer'])
        f.write("<hr><small>Powerd By: bones7456, check new version at ")
        f.write("<a href=\"http://li2z.cn/?s=SimpleHTTPServerWithUpload\">")
        f.write("here</a>.</small></body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def deal_post_data(self):
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line)
        if not fn:
            return (False, "Can't find out file name...")
        path = self.translate_path(self.path)
        fn = os.path.join(path, fn[0])
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")

        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, "File '%s' upload success!" % fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")

    def send_head(self):
        """Common code for GET and HEAD commands.
        This sends the response code and MIME headers.
        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
        """
        path = self.translate_path(self.path)
        url_path = urlparse(self.path)

        parent_dir = "/".join(url_path.path.split("/")[0:-1])+"/"
        query_components = parse_qs(url_path.query)
        item = None
        itemcontent = None
        if "item" in query_components:
            item = query_components["item"]
        if "itemcontent" in query_components:
            itemcontent = query_components["itemcontent"]

        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            else:
                return self.list_directory(path, url_path)
        ctype = "text/html"
        try:
            if(item != None):
                f = StringIO()
                f.write("""
<html>
    <head></head>
    <body>
                """)
                with open(path, 'rb') as warcstream:
                    i = 0
                    for record in ArchiveIterator(warcstream):
                        i = i + 1
                        if(str(i) == item[0]):
                            f.write("<b>FilePath:</b> {0}<br/>".format(url_path.path.split("/")[-1]))
                            if(record.format == "arc"):
                                url = record.rec_headers.get_header('uri')
                            else:
                                url = record.rec_headers.get_header('WARC-Target-URI')
                            f.write("<b>Record:</b> ({0}) {1}<br/>".format(
                                record.rec_type,
                                url
                            ))
                            f.write("<b>Record Number:</b> {0}".format(i))
                            f.write("<h2>(W)ARC Headers</h2>")
                            f.write("<b>Format:</b> {0} <br />".format(record.format))
                            if record.rec_headers != None:
                                for header in record.rec_headers.headers:
                                    f.write("<b>{0}:</b> {1} <br/>".format(str(header[0]),cgi.escape(str(header[1]))))
                            else:
                                f.write("No WARC Headers <br/>")

                            f.write("<h2>HTTP Headers</h2>")
                            if record.http_headers != None:
                                f.write("<b>{0}:</b> {1} <br/>".format("Status Code", record.http_headers.statusline))
                                for header in record.http_headers.headers:
                                    f.write("<b>{0}:</b> {1} <br/>".format(str(header[0]),str(header[1])))
                            else:
                                f.write("No HTTP Headers <br/>")

                            if(record.http_headers != None and
                                record.http_headers.get_header('Content-Type') != None and
                                record.http_headers.get_header('Content-Type')[0:5] == "image"):
                                f.write("<h2>Content (Image)</h2>")
                                raw_content = record.raw_stream.read()
                                if(raw_content == ""):
                                    f.write("<pre><code>No content in record</code></pre>".format(raw_content))
                                else:
                                    f.write("<a href=\"?itemcontent={0}\">Open Content</a><br/>".format(i))
                                    byte_arr = base64.b64encode(raw_content)
                                    f.write("""<img src="data:image/png;base64,{0}" />""".format(byte_arr))
                            else:
                                f.write("<h2>Content</h2>")

                                unreadable_coding = False

                                raw_content = cgi.escape(record.content_stream().read())
                                if(raw_content == ""):
                                    raw_content = cgi.escape(record.raw_stream.read())
                                if(raw_content == ""):
                                    raw_content = "No content in record."
                                else:
                                    f.write("<a href=\"?itemcontent={0}\">Open Content</a>".format(i))
                                f.write("<pre><code>{0}</code></pre>".format(raw_content))
                                break



                f.write("""
    </body>
</html>
                """)
            elif(itemcontent != None):
                f = StringIO()
                with open(path, 'rb') as warcstream:
                    i = 0
                    for record in ArchiveIterator(warcstream):
                        i = i + 1
                        if(str(i) == itemcontent[0]):
                            f.write(record.raw_stream.read())
                            if(record.http_headers != None and record.http_headers.get_header('Content-Type') != None):
                                ctype=record.http_headers.get_header('Content-Type')
                            elif(record.rec_headers != None and record.rec_headers.get_header('Content-Type') != None):
                                ctype=record.rec_headers.get_header('Content-Type')
                            else:
                                ctype="application/octet-stream"
                            break
            else:
                f = StringIO()
                f.write("""
<html>
    <head>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
        <style>
        .recorditem {
            margin:5px;
            padding:4px;
            border:1px solid black;
        }

        .recorditem:hover {
            background-color: #d9e6f2;
        }
        </style>
    </head>
    <body>
        <div style="width:50%;height:100%;overflow-x:hidden;float:left;">
                """)
                f.write("""
            <a href="{0}">
                Go Back
            </a>
                    """.format(parent_dir))
                with open(path, 'rb') as warcstream:
                    i = 0
                    for record in ArchiveIterator(warcstream):
                        i = i + 1
                        if(record.format == "arc"):
                            url = record.rec_headers.get_header('uri')
                        else:
                            url = record.rec_headers.get_header('WARC-Target-URI')
                        f.write("""
            <div class="recorditem" onclick="changeContent('{2}')">
                {0}: {1}
            </div>
                        """.format(
                            record.rec_type,
                            url,
                            i
                        ))

                f.write("""
        </div>
        <div style="width:50%;height:100%;float:left;overflow:auto;">
            <div id="content-div" style="padding:10px;">
            </div>
        </div>
    </body>
    <script type="text/javascript">
        function changeContent(itemNum) {
            document.getElementById('content-div').innerHTML = 'Loading...';
            $("#content-div").load("?item=" + itemNum);
        }
    </script>
</html>
                """)
        except IOError:
            self.send_error(404, "File not found")
            return None
        except ArchiveLoadFailed:
            self.send_error(400, "File is not a (W)ARC file")
            return None

        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def list_directory(self, path, url_path):
        parent_path = "/".join(url_path.path.split("/")[0:-2])+"/"
        """Helper to produce a directory listing (absent index.html).
        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().
        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write("<hr>\n")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write("<input name=\"file\" type=\"file\"/>")
        f.write("<input type=\"submit\" value=\"upload\"/></form>\n")
        f.write("<hr>\n<a href=\"%s\">Back</a><ul>\n" % parent_path)
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n'
                    % (quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.
        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)
        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.
        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).
        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.
        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.
        Argument is a PATH (a filename).
        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.
        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.
        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })


def basicServer(HandlerClass = SimpleHTTPRequestHandler,
         ServerClass = BaseHTTPServer.HTTPServer):
    url = "http://localhost:8000"
    webbrowser.open(url,new=2)
    BaseHTTPServer.test(HandlerClass, ServerClass)

if __name__ == '__main__':
    print("Python version: {0}.{1}".format(sys.version_info[0],sys.version_info[1]))
    if sys.version_info[0] > 2 or (sys.version_info[0] == 2 and sys.version_info[1] < 7) :
        raise ValueError("Must be using Python 2.7+")
    basicServer()
