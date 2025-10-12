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
        Schema::create('plobin_ocr_requests', function (Blueprint $table) {
            $table->id();
            $table->uuid('request_id')->unique()->comment('고유 요청 ID');
            $table->string('original_filename')->comment('원본 파일명');
            $table->enum('file_type', ['image', 'pdf'])->comment('파일 타입');
            $table->unsignedBigInteger('file_size')->comment('파일 크기 (bytes)');
            $table->unsignedInteger('total_pages')->default(1)->comment('총 페이지 수');
            $table->enum('status', ['processing', 'completed', 'failed'])->default('processing')->comment('처리 상태');
            $table->decimal('overall_confidence', 5, 3)->nullable()->comment('전체 신뢰도');
            $table->unsignedInteger('total_blocks')->default(0)->comment('전체 블록 수');
            $table->decimal('processing_time', 10, 3)->nullable()->comment('처리 시간 (초)');
            $table->text('error_message')->nullable()->comment('오류 메시지');
            $table->timestamp('completed_at')->nullable()->comment('완료 시각');
            $table->timestamps();

            $table->index('request_id');
            $table->index('status');
            $table->index('created_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('plobin_ocr_requests');
    }
};
