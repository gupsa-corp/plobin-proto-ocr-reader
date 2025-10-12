<?php

namespace Tests\Feature\Ocr\ProcessImage\PythonApiError;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class Test extends TestCase
{
    use RefreshDatabase;

    public function test_Python_OCR_API가_오류를_반환하면_500_응답이_반환된다(): void
    {
        // Given: Python OCR API가 500 오류 응답을 반환하도록 Mock 설정
        Http::fake([
            'localhost:6003/process-image' => Http::response([
                'error' => 'Internal Server Error',
                'detail' => 'OCR 처리 중 오류가 발생했습니다.'
            ], 500)
        ]);

        // Given: 테스트용 이미지 파일 생성
        $file = UploadedFile::fake()->image('test.jpg');

        // When: 이미지 OCR 처리 API 호출
        $response = $this->postJson('/api/process-image', [
            'file' => $file
        ]);

        // Then: 500 서버 오류 응답 확인
        $response->assertStatus(500);

        // Then: Python OCR API가 호출되었는지 확인
        Http::assertSent(function ($request) {
            return $request->url() === 'http://localhost:6003/process-image';
        });
    }
}
