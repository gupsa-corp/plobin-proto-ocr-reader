<?php

namespace App\Http\Controllers\Ocr\ProcessImage;

/**
 * @OA\Schema(
 *     schema="ProcessImageResponse",
 *     title="이미지 OCR 처리 응답",
 *     @OA\Property(property="success", type="boolean", example=true),
 *     @OA\Property(property="message", type="string", example="OCR 처리가 완료되었습니다."),
 *     @OA\Property(
 *         property="data",
 *         type="object",
 *         @OA\Property(property="request_id", type="string", example="550e8400-e29b-41d4-a716-446655440000"),
 *         @OA\Property(property="status", type="string", example="completed"),
 *         @OA\Property(property="original_filename", type="string", example="document.jpg"),
 *         @OA\Property(property="file_type", type="string", example="image"),
 *         @OA\Property(property="file_size", type="integer", example=1024000),
 *         @OA\Property(property="total_pages", type="integer", example=1),
 *         @OA\Property(property="processing_time", type="number", format="float", example=2.354),
 *         @OA\Property(property="processing_url", type="string", example="/requests/550e8400-e29b-41d4-a716-446655440000")
 *     )
 * )
 */
class Response
{
    public bool $success;
    public string $message;
    public array $data;

    public function __construct(array $pythonResponse)
    {
        $this->success = true;
        $this->message = 'OCR 처리가 완료되었습니다.';
        $this->data = $pythonResponse;
    }
}
