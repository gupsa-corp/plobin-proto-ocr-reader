<?php

namespace Tests\Feature\Ocr\ProcessImage\ValidationFail;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Tests\TestCase;

class Test extends TestCase
{
    use RefreshDatabase;

    public function test_파일이_없으면_유효성_검사가_실패한다(): void
    {
        // When: 파일 없이 API 호출
        $response = $this->postJson('/api/process-image', [
            'merge_blocks' => true,
            'merge_threshold' => 30
        ]);

        // Then: 422 유효성 검사 실패 응답
        $response->assertStatus(422)
            ->assertJsonValidationErrors(['file']);
    }

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

    public function test_병합_임계값이_범위를_벗어나면_유효성_검사가_실패한다(): void
    {
        // Given: 유효한 이미지 파일
        $file = UploadedFile::fake()->image('test.jpg');

        // When: 잘못된 병합 임계값으로 API 호출
        $response = $this->postJson('/api/process-image', [
            'file' => $file,
            'merge_threshold' => 200  // max: 100
        ]);

        // Then: 422 유효성 검사 실패 응답
        $response->assertStatus(422)
            ->assertJsonValidationErrors(['merge_threshold']);
    }
}
