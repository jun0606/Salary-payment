#!/usr/bin/env python3
"""
세무 프로그램용 저울 아이콘 생성 스크립트
상업용 무료 저울 이모지(⚖️)를 사용해서 .ico 파일 생성
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_scale_icon():
    """
    저울 이모지(⚖️)를 사용해서 아이콘 생성
    여러 사이즈로 생성하여 .ico 파일로 저장
    """
    print("저울 아이콘 생성 시작...")

    # 아이콘 사이즈들 (Windows ico 표준)
    sizes = [16, 32, 48, 64]

    # 저울 이모지
    scale_emoji = "⚖️"

    # 기본 배경색 (투명)
    background_color = (255, 255, 255, 0)  # RGBA 투명

    # 각 사이즈별 이미지 생성
    images = []
    for size in sizes:
        # RGBA 모드로 새 이미지 생성 (투명 배경)
        img = Image.new('RGBA', (size, size), background_color)
        draw = ImageDraw.Draw(img)

        try:
            # 시스템 기본 폰트 사용 (Segoe UI Emoji가 있으면 사용)
            try:
                # Windows의 경우 Segoe UI Emoji 폰트 시도
                font = ImageFont.truetype("seguiemj.ttf", size)
            except OSError:
                try:
                    # macOS의 경우 Apple Color Emoji 시도
                    font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", size)
                except OSError:
                    # Linux나 기타 시스템의 경우 기본 폰트 사용
                    font = ImageFont.load_default()

            # 텍스트 크기 계산을 위한 bbox
            bbox = draw.textbbox((0, 0), scale_emoji, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 중앙 정렬 좌표 계산
            x = (size - text_width) // 2
            y = (size - text_height) // 2

            # 이모지 그리기
            draw.text((x, y), scale_emoji, fill=(0, 0, 0, 255), font=font)

        except Exception as e:
            print(f"폰트 로드 실패, 기본 방법 사용: {e}")
            # 폰트 실패 시 간단한 저울 모양 그리기
            # 저울 판
            draw.rectangle([size//4, size//2, size*3//4, size*3//4],
                         fill=(0, 0, 0, 255), outline=(0, 0, 0, 255))
            # 저울 팔
            draw.line([size//2, size//4, size//2, size//2],
                     fill=(0, 0, 0, 255), width=max(1, size//32))

        images.append(img)

    # .ico 파일로 저장
    icon_path = "icon.ico"
    if images:
        # 첫 번째 이미지(가장 큰 것)를 기본으로 사용
        images[0].save(icon_path, format='ICO', sizes=[(s, s) for s in sizes])
        print(f"저울 아이콘 생성 완료: {icon_path}")
        print(f"지원 사이즈: {sizes}")
        return icon_path
    else:
        print("아이콘 생성 실패")
        return None

def create_simple_scale_icon():
    """
    이모지가 실패할 경우를 대비한 간단한 저울 아이콘 생성
    """
    print("간단한 저울 아이콘 생성...")

    size = 64
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 저울 중앙 기둥
    draw.rectangle([size//2-2, size//4, size//2+2, size*3//4],
                 fill=(0, 0, 0, 255))

    # 저울 팔 (가로선)
    draw.line([size//4, size//3, size*3//4, size//3],
             fill=(0, 0, 0, 255), width=3)

    # 저울 추
    draw.ellipse([size//4-5, size//3-5, size//4+5, size//3+5],
                fill=(0, 0, 0, 255))
    draw.ellipse([size*3//4-5, size//3-5, size*3//4+5, size//3+5],
                fill=(0, 0, 0, 255))

    # 저울 판
    draw.rectangle([size//4-8, size//2, size//4+8, size*3//4],
                 fill=(0, 0, 0, 255))
    draw.rectangle([size*3//4-8, size//2, size*3//4+8, size*3//4],
                 fill=(0, 0, 0, 255))

    icon_path = "icon.ico"
    img.save(icon_path, format='ICO')
    print(f"간단한 저울 아이콘 생성 완료: {icon_path}")
    return icon_path

if __name__ == "__main__":
    try:
        icon_path = create_scale_icon()
        if not icon_path:
            icon_path = create_simple_scale_icon()
        print(f"최종 아이콘 파일: {icon_path}")
    except Exception as e:
        print(f"아이콘 생성 중 오류: {e}")
        # 최후의 수단으로 간단한 아이콘 생성
        try:
            create_simple_scale_icon()
        except Exception as e2:
            print(f"간단한 아이콘 생성도 실패: {e2}")
