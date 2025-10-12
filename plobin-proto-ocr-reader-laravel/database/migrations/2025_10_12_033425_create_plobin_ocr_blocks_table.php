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
        Schema::create('plobin_ocr_blocks', function (Blueprint $table) {
            $table->id();
            $table->foreignId('page_id')->constrained('plobin_ocr_pages')->onDelete('cascade')->comment('페이지 ID');
            $table->unsignedInteger('block_number')->comment('블록 번호');
            $table->text('text')->comment('인식된 텍스트');
            $table->decimal('confidence', 5, 3)->comment('신뢰도');
            $table->json('bbox')->comment('바운딩 박스 좌표');
            $table->enum('block_type', ['title', 'paragraph', 'table', 'list', 'other'])->comment('블록 타입');
            $table->string('image_path')->nullable()->comment('블록 이미지 경로');
            $table->timestamps();

            $table->index('page_id');
            $table->index('block_number');
            $table->index('block_type');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('plobin_ocr_blocks');
    }
};
