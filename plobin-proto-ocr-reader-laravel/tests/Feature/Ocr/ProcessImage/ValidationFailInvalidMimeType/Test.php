<?php

namespace Tests\Feature\Ocr\ProcessImage\ValidationFailInvalidMimeType;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Tests\TestCase;

class Test extends TestCase
{
    use RefreshDatabase;

    public function test_잘못된_파일_형식이면_유효성_검사가_실패한다(): void
    {
        // Given: PDF 파일 생성 (이미지가 아님)
        $file = UploadedFile::fake()->create('document.pdf', 1000, 'application/pdf');

        // When: PDF 파일로 이미지 OCR API 호출
        $response = $this->postJson('/api/process-image', [
            'file' => $file
        ]);

        // Then: 422 유효성 검사 실패 응답
        $response->assertStatus(422)
            ->assertJsonValidationErrors(['file']);
    }
}
