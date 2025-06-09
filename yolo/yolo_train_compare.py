import argparse
import glob
import logging
import os
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import pandas as pd
import torch
from ultralytics import YOLO
from ultralytics.engine.results import Results


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    model_path: str
    data_path: str
    model_name: str
    save_dir: str
    epochs: int = 78
    imgsz: int = 640
    batch: int = 8
    device: str = "cuda"
    workers: int = 0

    
class ModelTrainer:
    def __init__(self, config: ModelConfig):
        self.config = config

    def train(self) -> str:
        logger.info(f"--- Начинаем обучение модели {self.config.model_name} ---")
        try:
            model = YOLO(self.config.model_path)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            results = model.train(
                data=self.config.data_path,
                epochs=self.config.epochs,
                imgsz=self.config.imgsz,
                batch=self.config.batch,
                device=self.config.device,
                workers=self.config.workers,
                name=f"train_{self.config.model_name}",
                project=self.config.save_dir,
                verbose=True
            )

            weights_dir = self._get_weights_dir(results, model)
            best_weights = os.path.join(weights_dir, "weights", "best.pt")
            logger.info(f"Best weights saved at: {best_weights}")
            return best_weights

        except Exception as e:
            logger.error(f"Ошибка при обучении модели: {str(e)}", exc_info=True)
            raise

    def _get_weights_dir(self, results, model) -> str:
        if hasattr(results, "save_dir"):
            return results.save_dir
        elif hasattr(model, "trainer") and hasattr(model.trainer, "save_dir"):
            return model.trainer.save_dir
        return os.path.join(self.config.save_dir, f"train_{self.config.model_name}")


class ModelEvaluator:
    def __init__(self, model_path: str):
        # Инициализируем модель только один раз при создании экземпляра
        self.model = YOLO(model_path).to('cpu')

    def evaluate(self, test_image_path: str, save_vis_dir: Optional[str] = None, prefix: str = "", device: str = "cpu") -> Dict[str, Any]:
        # Убедитесь, что device передается в метод model()
        try:
            # Устранена дублирующая строка results = self.model(test_image_path)
            results = self.model(test_image_path, device=device) 
            metrics = {}
            no_tumor_data = None

            for idx, result in enumerate(results):
                if hasattr(result, 'boxes') and len(result.boxes) > 0:
                    best_box, class_name = self._process_detection(result)

                    if class_name in ['Glioma', 'Meningioma', 'Pituitary']:
                        logger.info(f"🟢 Выбранный класс: {class_name}")
                        self._save_prediction(best_box, result, test_image_path, save_vis_dir, prefix, idx)
                    else:
                        no_tumor_data = (best_box, result, idx, class_name)

                    metrics.update(self._calculate_metrics(best_box))
                else:
                    logger.warning("Нет боксов для оценки.")
                    metrics.update({'avg_confidence': 'N/A', 'max_confidence': 'N/A'})

            if no_tumor_data:
                logger.info(f"🔴 Сохраняем No tumor в конце: {no_tumor_data[3]}")
                self._save_prediction(
                    best_box=no_tumor_data[0],
                    result=no_tumor_data[1],
                    test_image_path=test_image_path,
                    save_vis_dir=save_vis_dir,
                    prefix=prefix,
                    idx=no_tumor_data[2])

            return metrics

        except Exception as e:
            logger.error(f"Ошибка при оценке модели: {str(e)}", exc_info=True)
            raise

    def _process_detection(self, result) -> Tuple[Any, str]:
        confs = result.boxes.conf.cpu().numpy()
        max_idx = confs.argmax()
        best_box = result.boxes[max_idx:max_idx+1]
        class_id = int(best_box.cls.cpu().numpy()[0])
        return best_box, result.names[class_id]

    def _calculate_metrics(self, best_box) -> Dict[str, float]:
        conf = best_box.conf.cpu().numpy()[0]
        return {'avg_confidence': conf, 'max_confidence': conf}

    def _save_prediction(self, best_box: Any, result: Results, test_image_path: str, 
                         save_vis_dir: Optional[str], prefix: str, idx: int) -> None:
        # Создаем новую фигуру и оси для каждого изображения
        # Размер figsize и dpi можно настроить, если нужно более высокое разрешение
        fig, ax = plt.subplots(figsize=(result.orig_img.shape[1] / 100, result.orig_img.shape[0] / 100), dpi=100)
        
        try:
            # Создаем новый объект Results с выбранным боксом для plot
            best_result = Results(
                orig_img=result.orig_img,
                path=result.path,
                names=result.names
            )
            best_result.boxes = best_box
            best_result.masks = None # Убедитесь, что маски не используются, если не нужны
            best_result.probs = None # Убедитесь, что probs не используются, если не нужны

            # Получаем аннотированный кадр (numpy array)
            annotated_frame = best_result.plot()
            
            # Отображаем его на созданных осях
            ax.imshow(annotated_frame)
            ax.axis('off') # Убираем оси

            if save_vis_dir:
                os.makedirs(save_vis_dir, exist_ok=True)
                class_id = int(best_box.cls.cpu().numpy()[0])
                class_name = result.names[class_id]
                file_basename = os.path.basename(test_image_path).replace('.', f'_pred_{idx+1}.')
                outname = f"{class_name}_{file_basename}"
                save_path = os.path.join(save_vis_dir, outname)
                
                # Сохраняем текущую фигуру (fig)
                fig.savefig(save_path, bbox_inches='tight', pad_inches=0)
                logger.info(f"Сохранено: {save_path}")

        except Exception as e:
            logger.error(f"Ошибка при сохранении предсказания: {str(e)}", exc_info=True)
            raise
        finally:
            # ОЧЕНЬ ВАЖНО: Закрыть фигуру, чтобы освободить ресурсы Matplotlib после использования
            plt.close(fig) 


class ModelComparator:
    @staticmethod
    def compare(model1_path: str, model2_path: str, model1_name: str, model2_name: str, 
                test_image_path: str, save_vis_dir: Optional[str] = None) -> Optional[str]:
        try:
            logger.info("\n--- Сравнение моделей ---")
            evaluator1 = ModelEvaluator(model1_path)
            evaluator2 = ModelEvaluator(model2_path)

            metrics1 = evaluator1.evaluate(test_image_path, save_vis_dir, prefix=model1_name + "_")
            metrics2 = evaluator2.evaluate(test_image_path, save_vis_dir, prefix=model2_name + "_")

            comparison_df = pd.DataFrame({
                'Metric': ['Average Confidence', 'Max Confidence'],
                model1_name: [metrics1.get('avg_confidence', 'N/A'), metrics1.get('max_confidence', 'N/A')],
                model2_name: [metrics2.get('avg_confidence', 'N/A'), metrics2.get('max_confidence', 'N/A')]
            })

            logger.info("\nСравнение метрик:")
            logger.info(comparison_df)

            if 'avg_confidence' in metrics1 and 'avg_confidence' in metrics2:
                # Убедимся, что сравниваем числовые значения, если они 'N/A'
                conf1 = metrics1['avg_confidence'] if isinstance(metrics1['avg_confidence'], (int, float)) else -1
                conf2 = metrics2['avg_confidence'] if isinstance(metrics2['avg_confidence'], (int, float)) else -1

                if conf1 > conf2:
                    logger.info(f"\nЛучшая модель: {model1_name} (средний confidence: {metrics1['avg_confidence']:.2f})")
                    return model1_path
                else:
                    logger.info(f"\nЛучшая модель: {model2_name} (средний confidence: {metrics2['avg_confidence']:.2f})")
                    return model2_path
            else:
                logger.warning("\nНе удалось сравнить модели по confidence. Проверьте наличие детекций.")
                return None

        except Exception as e:
            logger.error(f"Ошибка при сравнении моделей: {str(e)}", exc_info=True)
            raise


class InferencePipeline:
    @staticmethod
    def run_inference(best_model: str, media_root: str, single_folder_id: Optional[str] = None, device: str = "cpu") -> None:
        try:
            logger.info(f"\n=== Инференс лучшей модели: {best_model} ===")
            evaluator = ModelEvaluator(best_model)
            # ВАЖНО: УДАЛЕНА строка evaluator.model = YOLO(best_model), 
            # так как модель уже инициализируется в ModelEvaluator.__init__

            if single_folder_id:
                target_dir = os.path.join(media_root, single_folder_id, "raw")
                if not os.path.exists(target_dir):
                    logger.error(f"Папка {target_dir} не найдена!")
                    raise FileNotFoundError(f"Folder not found: {target_dir}")
                all_raw_images = glob.glob(os.path.join(target_dir, "*.png"))
                logger.info(f"Инференс только для папки: {single_folder_id}/raw")
            else:
                all_raw_images = glob.glob(os.path.join(media_root, "*", "raw", "*.png"))
                logger.info(f"Инференс для всех папок в: {media_root}")

            if not all_raw_images:
                logger.error("Не найдено изображений для инференса!")
                raise FileNotFoundError("No images found for inference")

            for img_path in all_raw_images:
                base_dir = os.path.dirname(os.path.dirname(img_path))
                predict_dir = os.path.join(base_dir, "predict")
                os.makedirs(predict_dir, exist_ok=True)
                logger.info(f"\n--- Предикт для {img_path} ---")
                evaluator.evaluate(
                    test_image_path=img_path,
                    save_vis_dir=predict_dir,
                    prefix="",
                    device=device) # Передаем device

            logger.info("\nВсе предсказания завершены и сохранены.")

        except Exception as e:
            logger.error(f"Ошибка при выполнении инференса: {str(e)}", exc_info=True)
            raise


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--predict_only", action="store_true", help="Только предикт (по умолчанию включен)")
        parser.add_argument("--data_path", type=str, help="Путь к data.yaml")
        parser.add_argument("--model1_name", type=str, default="yolo11n")
        parser.add_argument("--model1_weights", type=str, help="Веса первой модели")
        parser.add_argument("--model2_name", type=str, default="yolov8n")
        parser.add_argument("--model2_weights", type=str, help="Веса второй модели")
        parser.add_argument("--epochs", type=int, default=30)
        parser.add_argument("--imgsz", type=int, default=640)
        parser.add_argument("--batch", type=int, default=8)
        parser.add_argument("--media_root", type=str, default="media/png", help="Корень с media/png/001, 002, ...")
        parser.add_argument("--yolo_dir", type=str, default="media/yolo/yoloruns", help="Куда сохранять веса и runs YOLO")
        parser.add_argument("--single_folder_id", type=str, help="ID папки для инференса (например, 007)")
        args = parser.parse_args()

        save_root = args.yolo_dir
        os.makedirs(save_root, exist_ok=True)

        best_model_file = os.path.join(save_root, "best_model.txt")

        if not os.path.isfile(best_model_file):
            logger.info("\n=== Начинаем обучение, так как нет best_model.txt ===")

            trainer1 = ModelTrainer(ModelConfig(
                model_path=args.model1_weights,
                data_path=args.data_path,
                model_name=args.model1_name,
                save_dir=save_root,
                epochs=args.epochs,
                imgsz=args.imgsz,
                batch=args.batch
            ))
            model1_weights = trainer1.train()

            trainer2 = ModelTrainer(ModelConfig(
                model_path=args.model2_weights,
                data_path=args.data_path,
                model_name=args.model2_name,
                save_dir=save_root,
                epochs=args.epochs,
                imgsz=args.imgsz,
                batch=args.batch
            ))
            model2_weights = trainer2.train()

            test_images = glob.glob("media/png/testimage/*.png")
            if not test_images:
                logger.error("Нет тестового изображения в media/png/testimage!")
                raise FileNotFoundError("No test images found")

            best_model = ModelComparator.compare(
                model1_path=model1_weights,
                model2_path=model2_weights,
                model1_name=args.model1_name,
                model2_name=args.model2_name,
                test_image_path=test_images[0],
                save_vis_dir=None
            )

            with open(best_model_file, "w") as f:
                f.write(best_model if best_model else "")
        else:
            with open(best_model_file, "r") as f:
                best_model = f.read().strip()

        if best_model:
            InferencePipeline.run_inference(
                best_model=best_model,
                media_root=args.media_root,
                single_folder_id=args.single_folder_id
            )

    except Exception as e:
        logger.error(f"Критическая ошибка в main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()