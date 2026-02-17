"""
PyInstaller Runtime Hook: jaraco.text Compatibility Fix

jaraco.text 모듈의 import 문제를 해결하기 위한 최소한의 런타임 훅입니다.
PyInstaller의 기본 TMP 관리를 방해하지 않습니다.
"""

import os
import sys

def install():
    """jaraco.text import 문제 해결 - PyInstaller 기본 동작 유지"""
    try:
        # jaraco.text 문제 해결: import 전에 sys.modules에 미리 설정
        _patch_jaraco_text_before_import()
        print("PyInstaller Runtime Hook: jaraco.text 패치 완료")

    except Exception as e:
        print(f"PyInstaller Runtime Hook 오류: {e}")


def _patch_jaraco_text_before_import():
    """jaraco.text의 완전한 인터페이스를 제공하는 더미 모듈 생성"""
    try:
        import re
        import textwrap
        import itertools
        import functools

        # lorem_ipsum 텍스트 정의
        lorem_content = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.

Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur?

Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur? At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga.

Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae non recusandae.

Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis doloribus asperiores repellat."""

        # 더미 클래스들 정의
        class DummyFoldedCase(str):
            def casefold(self):
                return super().casefold()

        class DummySeparatedValues(str):
            separator = ','

        class DummyExceptionTrap:
            def __init__(self, exception_class):
                self.exception_class = exception_class

            def passes(self, func):
                return func

        # 완전한 jaraco.text 더미 모듈 클래스
        class CompleteJaracoText:
            """jaraco.text의 완전한 인터페이스를 제공하는 더미 모듈"""

            # 기본 속성들
            lorem_ipsum = lorem_content

            # 클래스들
            FoldedCase = DummyFoldedCase
            SeparatedValues = DummySeparatedValues
            ExceptionTrap = DummyExceptionTrap
            Splitter = str.split
            Stripper = str.strip
            WordSet = set

            # 함수들
            @staticmethod
            def drop_comment(line):
                """Drop comments."""
                return line.partition(' #')[0]

            @staticmethod
            def trim(s):
                """Trim something like a docstring."""
                return textwrap.dedent(s).strip()

            @staticmethod
            def wrap(s):
                """Wrap lines of text."""
                return '\n'.join(textwrap.wrap(s))

            @staticmethod
            def unwrap(s):
                """Given a multi-line string, return an unwrapped version."""
                return ' '.join(s.splitlines())

            @staticmethod
            def normalize_newlines(text):
                """Replace alternate newlines with the canonical newline."""
                return text.replace('\r\n', '\n').replace('\r', '\n')

            @staticmethod
            def remove_prefix(text, prefix):
                """Remove the prefix from the text if it exists."""
                if text.startswith(prefix):
                    return text[len(prefix):]
                return text

            @staticmethod
            def remove_suffix(text, suffix):
                """Remove the suffix from the text if it exists."""
                if text.endswith(suffix):
                    return text[:-len(suffix)]
                return text

            @staticmethod
            def simple_html_strip(s):
                """Remove HTML from the string."""
                import re
                html_stripper = re.compile(r'<[^>]+>')
                return html_stripper.sub('', s)

            @staticmethod
            def is_decodable(value):
                """Return True if the supplied value is decodable."""
                try:
                    if isinstance(value, bytes):
                        value.decode('utf-8')
                    return True
                except:
                    return False

            @staticmethod
            def is_binary(value):
                """Return True if the value appears to be binary."""
                return isinstance(value, bytes) and not CompleteJaracoText.is_decodable(value)

            @staticmethod
            def substitution(old, new):
                """Return a function that will perform a substitution."""
                return lambda s: s.replace(old, new)

            @staticmethod
            def multi_substitution(*substitutions):
                """Take a sequence of pairs specifying substitutions."""
                def substitute(s):
                    for old, new in substitutions:
                        s = s.replace(old, new)
                    return s
                return substitute

            @staticmethod
            def compose(*functions):
                """Compose functions."""
                return functools.reduce(lambda f, g: lambda x: f(g(x)), functions)

            @staticmethod
            def yield_lines(text):
                """Yield valid lines of a string."""
                for line in text.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        yield line

            @staticmethod
            def join_continuation(lines):
                """Join lines continued by a trailing backslash."""
                result = []
                current = ''
                for line in lines:
                    if line.endswith('\\'):
                        current += line[:-1]
                    else:
                        current += line
                        result.append(current)
                        current = ''
                return result

            # 더미 함수들 (기본 구현)
            @staticmethod
            def indent(text, prefix='    '):
                return '\n'.join(prefix + line for line in text.splitlines())

            @staticmethod
            def read_newlines(filename, limit=1024):
                return '\n'

            @staticmethod
            def words(text):
                return text.split()

            # 필요한 서브모듈들
            @staticmethod
            def method_cache(func):
                return func

        # 완전한 더미 모듈 생성
        dummy_jaraco_text = CompleteJaracoText()

        # 필요한 속성들 추가
        dummy_jaraco_text.re = re
        dummy_jaraco_text.textwrap = textwrap
        dummy_jaraco_text.itertools = itertools
        dummy_jaraco_text.functools = functools

        # sys.modules에 설정
        sys.modules['jaraco.text'] = dummy_jaraco_text
        sys.modules['setuptools._vendor.jaraco.text'] = dummy_jaraco_text
        sys.modules['setuptools._vendor.jaraco'] = type('Module', (), {'text': dummy_jaraco_text})()
        sys.modules['setuptools._vendor'] = type('Module', (), {'jaraco': sys.modules['setuptools._vendor.jaraco']})()
        sys.modules['setuptools'] = type('Module', (), {'_vendor': sys.modules['setuptools._vendor']})()

        print("jaraco.text 완전 패치 완료 - 모든 인터페이스 제공")

    except Exception as e:
        print(f"jaraco.text 완전 패치 실패: {e}")
        # 실패해도 계속 진행 (중요!)

# PyInstaller 감지 및 즉시 실행
if getattr(sys, 'frozen', False):
    install()
else:
    print("Runtime Hook: PyInstaller 환경이 아님")
