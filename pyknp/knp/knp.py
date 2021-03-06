#-*- encoding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import absolute_import
from pyknp import Juman
from pyknp import Socket, Subprocess  
from pyknp import BList
import os
import sys
import unittest
import six
import distutils.spawn


class KNP(object):
    """ KNPを用いて構文解析を行う/KNPの解析結果を読み取るモジュール

    Args:
        command (str): KNPコマンド
        option (str): KNP解析オプション 
                        (詳細解析結果を出力する-tabは必須。 
                        省略・照応解析を行う -anaphora, 格解析を行わず構文解析のみを行う -dpnd など)
        rcfile (str): KNP設定ファイルへのパス
        pattern (str): KNP出力の終端記号
        jumancommand (str): JUMANコマンド
        jumanrcfile (str): JUMAN設定ファイルへのパス
        jumanpp (bool): JUMAN++を用いるかJUMANを用いるか
    """

    def __init__(self, command='knp', server=None, port=31000, timeout=60,
                 option='-tab', rcfile='', pattern=r'EOS',
                 jumancommand='jumanpp', jumanrcfile='', jumanpp=True):
        self.command = command
        self.server = server
        self.port = port
        self.timeout = timeout
        self.option = option.split()
        self.rcfile = rcfile
        self.pattern = pattern
        self.socket = None
        self.subprocess = None
        self.jumanpp = jumanpp

        if self.rcfile and not os.path.isfile(os.path.expanduser(self.rcfile)):
            raise Exception("Can't read rcfile (%s)!" % self.rcfile)
        if distutils.spawn.find_executable(self.command) is None:
            raise Exception("Can't find KNP command: %s" % self.command)

        self.juman = Juman(command=jumancommand, rcfile=jumanrcfile, jumanpp=self.jumanpp)

    def knp(self, sentence):
        """ parse関数と同じ """
        self.parse(sentence)

    def parse(self, sentence):
        """
        文字列を入力として構文解析を行い、文節列オブジェクトを返す

        Args:
            sentence (str): 文を表す文字列

        Returns:
            BList: 文節列オブジェクト
        """
        assert(isinstance(sentence, six.text_type))
        juman_lines = self.juman.juman_lines(sentence)
        juman_str = "%s%s" % (juman_lines, self.pattern)
        if not self.socket and not self.subprocess:
            if self.server is not None:
                self.socket = Socket(
                    self.server, self.port, "RUN -tab -normal\n")
            else:
                command = [self.command] + self.option
                if self.rcfile:
                    command.extend(['-r', self.rcfile])
                self.subprocess = Subprocess(command)

        if self.socket:
            knp_lines = self.socket.query(juman_str, pattern=r'^%s$'%(self.pattern))
        else:
            knp_lines = self.subprocess.query(juman_str, pattern=r'^%s$'%(self.pattern))
        return BList(knp_lines, self.pattern)

    def result(self, input_str):
        """
        ある文に関するKNP解析結果を文節列オブジェクトに変換する

        Args:
            input_str (str): ある文に関するKNPの出力結果

        Returns:
            BList: 文節列オブジェクト
        """
        return BList(input_str, self.pattern)


class KNPTest(unittest.TestCase):

    def setUp(self):
        self.knp = KNP()

    def test_dpnd(self):
        result = self.knp.parse("赤い花が咲いた。")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].parent.bnst_id, 1)
        self.assertEqual(len(result[1].children), 1)
        self.assertEqual(result[1].children[0].bnst_id, 0)
        self.assertEqual(result[1].parent.bnst_id, 2)
        self.assertEqual(result[2].parent, None)

    def test_mrph(self):
        result = self.knp.parse("赤い花が咲いた。")
        self.assertEqual(
            ''.join([mrph.midasi for mrph in result[0].mrph_list()]), '赤い')
        self.assertEqual(
            ''.join([mrph.midasi for mrph in result[1].mrph_list()]), '花が')
        self.assertEqual(
            ''.join([mrph.midasi for mrph in result[2].mrph_list()]), '咲いた。')

    def test_mrph2(self):
        result = self.knp.parse("エネルギーを素敵にENEOS")
        self.assertEqual(
            ''.join([mrph.midasi for mrph in result[0].mrph_list()]), 'エネルギーを')
        self.assertEqual(
            ''.join([mrph.midasi for mrph in result[1].mrph_list()]), '素敵に')
        self.assertEqual(
            ''.join([mrph.midasi for mrph in result[2].mrph_list()]), 'ENEOS')

if __name__ == '__main__':
    unittest.main()
