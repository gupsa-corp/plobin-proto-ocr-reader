<?php

namespace App\Http\Controllers\Ocr\ProcessImage;

use App\Http\Controllers\Controller as BaseController;
use App\Services\Ocr\ProcessImage\Service;
use Illuminate\Http\JsonResponse;

/**
 * @OA\Post(
 *     path="/api/process-image",
 *     tags={"OCR Processing"},
 *     summary="이미지 OCR 처리",
 *     description="업로드된 이미지 파일을 OCR 처리하여 텍스트 블록을 추출합니다.",
 *     @OA\RequestBody(
 *         required=true,
 *         @OA\MediaType(
 *             mediaType="multipart/form-data",
 *             @OA\Schema(
 *                 required={"file"},
 *                 @OA\Property(property="file", type="string", format="binary", description="이미지 파일"),
 *                 @OA\Property(property="merge_blocks", type="boolean", description="인접 블록 병합 여부", default=true),
 *                 @OA\Property(property="merge_threshold", type="integer", description="블록 병합 임계값 (픽셀)", default=30)
 *             )
 *         )
 *     ),
 *     @OA\Response(
 *         response=200,
 *         description="OCR 처리 성공",
 *         @OA\JsonContent(ref="#/components/schemas/ProcessImageResponse")
 *     ),
 *     @OA\Response(response=422, description="입력 데이터 유효성 검사 실패"),
 *     @OA\Response(response=500, description="서버 오류")
 * )
 */
class Controller extends BaseController
{
    public function __invoke(Request $request): JsonResponse
    {
        $service = new Service();
        $result = $service->execute(
            $request->file('file'),
            $request->input('merge_blocks', true),
            $request->input('merge_threshold', 30)
        );

        return response()->json(new Response($result));
    }
}
