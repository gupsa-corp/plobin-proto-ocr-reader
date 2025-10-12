<?php

namespace Tests\Feature\Ocr\ProcessImage\ValidationFailFileRequired;

use Illuminate\Foundation\Testing\RefreshDatabase;
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
}
