<?php

namespace Tests\Feature\Ocr\ProcessImage\Success;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class Test extends TestCase
{
    use RefreshDatabase;

    public function test_이미지_OCR_처리가_성공한다(): void
    {
        // Given: Python OCR API가 성공 응답을 반환하도록 Mock 설정
        Http::fake([
            'localhost:6003/process-image' => Http::response([
                'request_id' => '550e8400-e29b-41d4-a716-446655440000',
                'status' => 'completed',
                'original_filename' => 'test.jpg',
                'file_type' => 'image',
                'file_size' => 1024000,
                'total_pages' => 1,
                'processing_time' => 2.354,
                'processing_url' => '/requests/550e8400-e29b-41d4-a716-446655440000'
            ], 200)
        ]);

        // Given: 테스트용 이미지 파일 생성
        $file = UploadedFile::fake()->image('test.jpg', 800, 600)->size(1000);

        // When: 이미지 OCR 처리 API 호출
        $response = $this->postJson('/api/process-image', [
            'file' => $file,
            'merge_blocks' => true,
            'merge_threshold' => 30
        ]);

        // Then: 성공 응답 확인
        $response->assertStatus(200)
            ->assertJson([
                'success' => true,
                'message' => 'OCR 처리가 완료되었습니다.',
                'data' => [
                    'request_id' => '550e8400-e29b-41d4-a716-446655440000',
                    'status' => 'completed',
                    'original_filename' => 'test.jpg',
                    'file_type' => 'image'
                ]
            ]);

        // Then: Python OCR API가 호출되었는지 확인
        Http::assertSent(function ($request) {
            return $request->url() === 'http://localhost:6003/process-image' &&
                   $request->method() === 'POST';
        });
    }
}
