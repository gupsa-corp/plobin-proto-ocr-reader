<?php

namespace App\Http\Controllers\Ocr\ProcessPdf;

use Illuminate\Foundation\Http\FormRequest;

class Request extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'file' => 'required|file|mimes:pdf|max:51200',
            'merge_blocks' => 'nullable|boolean',
            'merge_threshold' => 'nullable|integer|min:1|max:100',
        ];
    }

    public function messages(): array
    {
        return [
            'file.required' => 'PDF 파일이 필요합니다.',
            'file.file' => '유효한 파일이 아닙니다.',
            'file.mimes' => 'PDF 파일만 지원됩니다.',
            'file.max' => '파일 크기는 50MB를 초과할 수 없습니다.',
            'merge_threshold.min' => '병합 임계값은 1 이상이어야 합니다.',
            'merge_threshold.max' => '병합 임계값은 100 이하여야 합니다.',
        ];
    }
}
