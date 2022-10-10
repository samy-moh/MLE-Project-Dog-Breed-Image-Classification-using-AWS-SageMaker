import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.models as models
import torchvision.transforms as transforms

import argparse
import torch.utils.data
import torch.utils.data.distributed
import logging
import os
import sys
import json
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def test(model, test_loader, criterion, device):
    '''
    TODO: Complete this function that can take a model and a 
          testing data loader and will get the test accuray/loss of the model
          Remember to include any debugging/profiling hooks that you might need
    '''
    model.eval()
    running_loss=0
    running_corrects=0
    
    for inputs, labels in test_loader:
        outputs=model(inputs)
        loss=criterion(outputs, labels)
        _, preds = torch.max(outputs, 1)
        running_loss += loss.item() * inputs.size(0)
        running_corrects += torch.sum(preds == labels.data).item()

    total_loss = running_loss / len(test_loader)
    total_acc = running_corrects / len(test_loader)

def train(model, train_loader, criterion, optimizer, epoch, device):
    '''
    TODO: Complete this function that can take a model and
          data loaders for training and will get train the model
          Remember to include any debugging/profiling hooks that you might need
    '''
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.train()
    
   
    for e in range(epoch):
        running_loss=0
        correct=0
        for data, target in train_loader:
            data=data.to(device)
            target=target.to(device)
            optimizer.zero_grad()
            pred = model(data)             #No need to reshape data since CNNs take image inputs
            loss = cost(pred, target)
            running_loss+=loss
            loss.backward()
            optimizer.step()
            pred=pred.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
    print(f"Epoch {e}: Loss {running_loss/len(train_loader.dataset)}, \
         Accuracy {100*(correct/len(train_loader.dataset))}%")
    
    return model

    
def net():
    '''
    TODO: Complete this function that initializes your model
          Remember to use a pretrained model
    '''
    model = models.resnet18(pretrained=True)

    for param in model.parameters():
        param.requires_grad = False   

    num_features=model.fc.in_features
    model.fc = nn.Sequential(
                   nn.Linear(num_features, 133))

    return model

def create_data_loaders(data, batch_size):
    '''
    This is an optional function that you may or may not need to implement
    depending on whether you need to use data loaders or not
    '''
    train_data_path = os.path.join(data, "train")
    test_data_path = os.path.join(data, "test")
    
    logger.info("Get train data loader")
    train_transform = transforms.Compose(
            [transforms.ToTensor(), transforms.Resize((224,224))]
        )
    train_data = torchvision.datasets.ImageFolder(root=train_data_path, transform=train_transform)
    train_loader = torch.utils.data.DataLoader(train_data, batch_size=batch_size, shuffle=True)
    
    logger.info("Get test data loader")
    test_transform = transforms.Compose(
            [transforms.ToTensor(), transforms.Resize((224,224))]
        )
    
    test_data = torchvision.datasets.ImageFolder(root=test_data_path, transform=test_transform)
    test_loader = torch.utils.data.DataLoader(test_data, batch_size=batch_size, shuffle=True)
    
    return train_loader , test_loader

def main(args):
    '''
    TODO: Initialize a model by calling the net function
    '''
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Running on Device {device}")
    
    
    model=net()
    model= model.to(device)
    '''
    TODO: Create your loss and optimizer
    '''
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(),  lr=args.lr)
    
    '''
    TODO: Call the train function to start training your model
    Remember that you will need to set up a way to get training data from S3
    '''
    train_loader = create_data_loaders(args.data_dir, args.batch_size)
    test_loader = create_data_loaders(args.data_dir, args.test_batch_size)
    
    
    for epoch in range(1, args.epochs +1 ):
        train(model, train_loader, criterion, optimizer, epoch, device)
        test(model, test_loader, criterion, device)
    '''
    TODO: Test the model to see its accuracy
    '''
    test(model, test_loader, criterion, device)
    
    '''
    TODO: Save the trained model
    '''
    logger.info("Saving the model.")
    path = os.path.join(model_dir, "model.pth")
    torch.save(model.cpu().state_dict(), path)
    

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    '''
    TODO: Specify all the hyperparameters you need to use to train your model.
    '''
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        metavar="N",
        help="input batch size for training (default: 64)",
    )
    parser.add_argument(
        "--test-batch-size",
        type=int,
        default=1000,
        metavar="N",
        help="input batch size for testing (default: 1000)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        metavar="N",
        help="number of epochs to train (default: 3)",
    )
    parser.add_argument(
        "--lr", type=float, default=0.01, metavar="LR", help="learning rate (default: 0.01)"
    )
    
    parser.add_argument("--model-dir", type=str, default=os.environ["SM_MODEL_DIR"])
    parser.add_argument("--data-dir", type=str, default=os.environ["SM_CHANNEL_TRAINING"])
    parser.add_argument("--output_dir", type=str, default=os.environ['SM_OUTPUT_DATA_DIR'])


    
    args=parser.parse_args()
    
    main(args)