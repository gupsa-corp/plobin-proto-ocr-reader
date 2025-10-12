<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('plobin_ocr_pages', function (Blueprint $table) {
            $table->id();
            $table->foreignId('request_id')->constrained('plobin_ocr_requests')->onDelete('cascade')->comment('요청 ID');
            $table->unsignedInteger('page_number')->comment('페이지 번호');
            $table->unsignedInteger('total_blocks')->default(0)->comment('페이지 블록 수');
            $table->decimal('average_confidence', 5, 3)->nullable()->comment('평균 신뢰도');
            $table->decimal('processing_time', 10, 3)->nullable()->comment('처리 시간 (초)');
            $table->string('original_image_path')->nullable()->comment('원본 이미지 경로');
            $table->string('visualization_path')->nullable()->comment('시각화 이미지 경로');
            $table->timestamps();

            $table->unique(['request_id', 'page_number']);
            $table->index('page_number');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('plobin_ocr_pages');
    }
};
