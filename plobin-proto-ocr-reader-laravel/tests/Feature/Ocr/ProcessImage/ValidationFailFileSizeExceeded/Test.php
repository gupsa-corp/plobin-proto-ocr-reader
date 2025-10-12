<?php

namespace Tests\Feature\Ocr\ProcessImage\ValidationFailFileSizeExceeded;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Tests\TestCase;

class Test extends TestCase
{
    use RefreshDatabase;

    public function test_파일_크기가_초과하면_유효성_검사가_실패한다(): void
    {
        // Given: 10MB 초과 이미지 파일 생성
        $file = UploadedFile::fake()->image('large.jpg')->size(11000);

        // When: 대용량 파일로 API 호출
        $response = $this->postJson('/api/process-image', [
            'file' => $file
        ]);

        // Then: 422 유효성 검사 실패 응답
        $response->assertStatus(422)
            ->assertJsonValidationErrors(['file']);
    }
}
