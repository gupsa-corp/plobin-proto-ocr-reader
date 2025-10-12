<?php

namespace App\Http\Controllers\Ocr\ProcessImage;

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
            'file' => 'required|file|mimes:jpeg,jpg,png,gif,webp|max:10240',
            'merge_blocks' => 'nullable|boolean',
            'merge_threshold' => 'nullable|integer|min:1|max:100',
        ];
    }

    public function messages(): array
    {
        return [
            'file.required' => '이미지 파일이 필요합니다.',
            'file.file' => '유효한 파일이 아닙니다.',
            'file.mimes' => '지원되는 이미지 형식: JPEG, JPG, PNG, GIF, WEBP',
            'file.max' => '파일 크기는 10MB를 초과할 수 없습니다.',
            'merge_threshold.min' => '병합 임계값은 1 이상이어야 합니다.',
            'merge_threshold.max' => '병합 임계값은 100 이하여야 합니다.',
        ];
    }
}
