<?php

use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

// OCR Processing
Route::post('/process-image', \App\Http\Controllers\Ocr\ProcessImage\Controller::class);
Route::post('/process-pdf', \App\Http\Controllers\Ocr\ProcessPdf\Controller::class);
