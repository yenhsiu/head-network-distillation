import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data.sampler import SubsetRandomSampler


def get_train_and_valid_loaders(data_dir_path, batch_size, normalizer, valid_rate, random_seed=1, shuffle=True):
    valid_comp_list = [transforms.ToTensor()]
    train_comp_list = [transforms.RandomCrop(32, padding=4), transforms.RandomHorizontalFlip(), transforms.ToTensor()]
    if normalizer is not None:
        valid_comp_list.append(normalizer)
        train_comp_list.append(normalizer)
    train_transformer = transforms.Compose(train_comp_list)
    valid_transformer = transforms.Compose(valid_comp_list)

    train_dataset = torchvision.datasets.CIFAR10(root=data_dir_path, train=True,
                                                 download=True, transform=train_transformer)
    valid_dataset = torchvision.datasets.CIFAR10(root=data_dir_path, train=True,
                                                 download=True, transform=valid_transformer)
    org_train_size = len(train_dataset)
    indices = list(range(org_train_size))
    train_end_idx = int(np.floor((1 - valid_rate) * org_train_size))
    if shuffle:
        np.random.seed(random_seed)
        np.random.shuffle(indices)

    train_indices, valid_indices = indices[:train_end_idx], indices[train_end_idx:]
    train_sampler = SubsetRandomSampler(train_indices)
    valid_sampler = SubsetRandomSampler(valid_indices)
    pin_memory = torch.cuda.is_available()
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, sampler=train_sampler,
                                               num_workers=2, pin_memory=pin_memory)
    valid_loader = torch.utils.data.DataLoader(valid_dataset, batch_size=batch_size, sampler=valid_sampler,
                                               num_workers=2, pin_memory=pin_memory)
    return train_loader, valid_loader


def get_test_transformer(normalizer, compression_type, compressed_size_str, org_size=(32, 32)):
    normal_list = [transforms.ToTensor()]
    if normalizer is not None:
        normal_list.append(normalizer)
    normal_transformer = transforms.Compose(normal_list)
    if compression_type is None or compressed_size_str is None:
        return normal_transformer

    hw = compressed_size_str.split(',')
    compressed_size = (int(hw[0]), int(hw[1]))
    if compression_type == 'base':
        comp_list = [transforms.Resize(compressed_size), transforms.Resize(org_size), transforms.ToTensor()]
        if normalizer is not None:
            comp_list.append(normalizer)
        return transforms.Compose(comp_list)
    return normal_transformer


def get_data_loaders(data_dir_path, compression_type=None, compressed_size_str=None, valid_rate=0.1, normalized=True):
    normalizer =\
        transforms.Normalize(mean=[0.4914, 0.4822, 0.4465], std=[0.2023, 0.1994, 0.2010]) if normalized else None
    train_loader, valid_loader = get_train_and_valid_loaders(data_dir_path, batch_size=128,
                                                             normalizer=normalizer, valid_rate=valid_rate)
    test_transformer = get_test_transformer(normalizer, compression_type, compressed_size_str)
    test_set = torchvision.datasets.CIFAR10(root=data_dir_path, train=False, download=True, transform=test_transformer)
    test_loader = torch.utils.data.DataLoader(test_set, batch_size=100, shuffle=False, num_workers=2,
                                              pin_memory=torch.cuda.is_available())
    return train_loader, valid_loader, test_loader
