<?php

namespace App\Services\Ocr\ProcessPdf;

use Illuminate\Support\Facades\Http;
use Illuminate\Http\UploadedFile;

class Service
{
    private string $pythonApiUrl;

    public function __construct()
    {
        $this->pythonApiUrl = config('services.python_ocr.url', 'http://localhost:6003');
    }

    public function execute(UploadedFile $file, bool $mergeBlocks = true, int $mergeThreshold = 30): array
    {
        $response = Http::asMultipart()
            ->attach('file', file_get_contents($file->getRealPath()), $file->getClientOriginalName())
            ->post("{$this->pythonApiUrl}/process-pdf", [
                'merge_blocks' => $mergeBlocks,
                'merge_threshold' => $mergeThreshold,
            ]);

        if ($response->failed()) {
            throw new \Exception("Python OCR API 호출 실패: " . $response->body());
        }

        return $response->json();
    }
}
