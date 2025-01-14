# cse546-cloudcomputing-scalable-face-recognition-system

As part of the CSE546: Cloud Computing course at Arizona State University, I dove deep into building a fully automated AWS-based solution that seamlessly handles concurrent facial recognition requests. The heart of this system is a sophisticated three-tier architecture featuring custom auto-scaling logic that dynamically manages up to 20 instances, scaling to zero during quiet periods – a perfect marriage of performance and cost efficiency. The system processes image requests through a deep learning model and stores results in cloud storage.

![](https://github.com/SarthakRana/cse546-cloudcomputing-scalable-face-recognition-system/blob/main/architecture.png)



## 🛠️ Architecture & Implementation:

👉 Designed a robust 3-tier architecture:

  ➡️ Web Tier: Single EC2 instance handling user requests
  ➡️ App Tier: Auto-scaling PyTorch-based ML processing fleet
  ➡️ Data Tier: S3-based persistent storage for scalability

👉 Implemented custom auto-scaling logic that dynamically scaled 0-20 instances

👉 Orchestrated asynchronous processing using SQS queues for reliable message handling

👉 Deployed deep learning models for real-time face recognition using PyTorch

## 🎓 Key Technical Highlights:

✅ Built an elastic face recognition pipeline handling 50+ concurrent requests

✅ Orchestrated a multi-tier architecture with custom auto-scaling logic

✅ Achieved blazing-fast processing times (under 3 minutes for 50 requests!)🚀

✅ Mastered AWS services (EC2, S3, SQS) for production-grade deployment

✅ Integrated PyTorch-based deep learning for real-time inference

The best part? Watching my cloud architecture smoothly scale from 0 to 20 instances based on demand was absolutely thrilling! 🎯 From managing cloud costs to implementing efficient auto-scaling algorithms, every hurdle taught me something valuable about production-grade cloud systems.
