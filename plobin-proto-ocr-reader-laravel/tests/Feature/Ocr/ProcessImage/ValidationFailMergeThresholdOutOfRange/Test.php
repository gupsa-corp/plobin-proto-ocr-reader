<?php

namespace Tests\Feature\Ocr\ProcessImage\ValidationFailMergeThresholdOutOfRange;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Tests\TestCase;

class Test extends TestCase
{
    use RefreshDatabase;

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
